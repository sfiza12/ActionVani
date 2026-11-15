"""Tests for the standalone in-memory session store."""

import asyncio
from datetime import datetime, timedelta, timezone

import pytest

from app.session_models import SessionStatus, SessionUpdate
from app.session_store import (
    DEFAULT_IDLE_TIMEOUT,
    InMemorySessionStore,
    SessionConflictError,
    SessionNotFoundError,
)


class FakeClock:
    def __init__(self) -> None:
        self.current = datetime(2030, 1, 1, tzinfo=timezone.utc)

    def __call__(self) -> datetime:
        return self.current

    def advance(self, duration: timedelta) -> None:
        self.current += duration


def test_session_ids_are_unique_server_generated_and_not_caller_supplied():
    async def scenario():
        store = InMemorySessionStore()
        with pytest.raises(TypeError):
            store.create_session(session_id="caller-selected")

        sessions = await asyncio.gather(*(store.create_session() for _ in range(12)))
        ids = [session.session_id for session in sessions]
        assert len(set(ids)) == len(ids)
        assert all(len(session_id) >= 32 for session_id in ids)

    asyncio.run(scenario())


def test_session_creation_and_retrieval_return_independent_copies():
    async def scenario():
        clock = FakeClock()
        store = InMemorySessionStore(clock=clock)
        source_draft = {"profile": {"city": "Delhi"}}
        created = await store.create_session(
            workflow_step="collecting",
            application_draft=source_draft,
        )

        assert created.status == SessionStatus.ACTIVE
        assert created.created_at == clock.current
        assert created.last_activity_at == clock.current
        assert created.expires_at == clock.current + DEFAULT_IDLE_TIMEOUT

        source_draft["profile"]["city"] = "Changed from input"
        created.application_draft["profile"]["city"] = "Changed outside store"
        retrieved = await store.get_session(created.session_id)
        assert retrieved is not None
        assert retrieved.application_draft == {"profile": {"city": "Delhi"}}
        retrieved.application_draft["profile"]["city"] = "Changed again"
        reread = await store.get_session(created.session_id)
        assert reread is not None
        assert reread.application_draft == {"profile": {"city": "Delhi"}}

    asyncio.run(scenario())


def test_sessions_are_isolated_from_each_other():
    async def scenario():
        store = InMemorySessionStore()
        first = await store.create_session(application_draft={"city": "Delhi"})
        second = await store.create_session(application_draft={"city": "Pune"})

        await store.update_session(
            first.session_id,
            SessionUpdate(application_draft_patch={"city": "Jaipur"}),
            expected_revision=0,
        )

        updated_first = await store.get_session(first.session_id)
        unchanged_second = await store.get_session(second.session_id)
        assert updated_first is not None and updated_first.application_draft["city"] == "Jaipur"
        assert unchanged_second is not None and unchanged_second.application_draft["city"] == "Pune"

    asyncio.run(scenario())


def test_partial_update_preserves_other_fields_and_advances_revisions():
    async def scenario():
        store = InMemorySessionStore()
        session = await store.create_session(
            workflow_step="collecting",
            application_draft={"name": "Example", "city": "Delhi"},
        )

        updated = await store.update_session(
            session.session_id,
            SessionUpdate(
                workflow_step="review",
                application_draft_patch={"city": "Jaipur"},
            ),
            expected_revision=0,
        )

        assert updated.workflow_step == "review"
        assert updated.application_draft == {"name": "Example", "city": "Jaipur"}
        assert updated.revision == 1
        assert updated.draft_revision == 1

    asyncio.run(scenario())


def test_stale_revision_cannot_overwrite_newer_session_data():
    async def scenario():
        store = InMemorySessionStore()
        session = await store.create_session(application_draft={"city": "Delhi"})
        await store.update_session(
            session.session_id,
            SessionUpdate(application_draft_patch={"city": "Jaipur"}),
            expected_revision=0,
        )

        with pytest.raises(SessionConflictError):
            await store.update_session(
                session.session_id,
                SessionUpdate(application_draft_patch={"city": "Mumbai"}),
                expected_revision=0,
            )

        current = await store.get_session(session.session_id)
        assert current is not None
        assert current.application_draft["city"] == "Jaipur"
        assert current.revision == 1

    asyncio.run(scenario())


def test_deletion_removes_session_and_is_idempotent():
    async def scenario():
        store = InMemorySessionStore()
        session = await store.create_session()

        assert await store.delete_session(session.session_id) is True
        assert await store.get_session(session.session_id) is None
        assert await store.delete_session(session.session_id) is False

    asyncio.run(scenario())


def test_expiry_uses_injected_clock_and_cleanup_removes_idle_sessions():
    async def scenario():
        clock = FakeClock()
        store = InMemorySessionStore(
            idle_timeout=timedelta(minutes=5),
            clock=clock,
        )
        expires_by_read = await store.create_session()
        expires_by_cleanup = await store.create_session()

        clock.advance(timedelta(minutes=4))
        refreshed = await store.get_session(expires_by_read.session_id)
        assert refreshed is not None
        assert refreshed.expires_at == clock.current + timedelta(minutes=5)

        clock.advance(timedelta(minutes=5, seconds=1))
        assert await store.get_session(expires_by_read.session_id) is None
        assert await store.cleanup_expired() == 1
        assert await store.get_session(expires_by_cleanup.session_id) is None

    asyncio.run(scenario())


def test_concurrent_updates_are_serialized_and_stale_writer_conflicts():
    async def scenario():
        store = InMemorySessionStore()
        session = await store.create_session(application_draft={"left": 0, "right": 0})

        async def update(key: str, value: int):
            try:
                return await store.update_session(
                    session.session_id,
                    SessionUpdate(application_draft_patch={key: value}),
                    expected_revision=0,
                )
            except SessionConflictError as error:
                return error

        results = await asyncio.gather(update("left", 1), update("right", 1))
        successes = [result for result in results if not isinstance(result, Exception)]
        conflicts = [result for result in results if isinstance(result, SessionConflictError)]
        current = await store.get_session(session.session_id)

        assert len(successes) == 1
        assert len(conflicts) == 1
        assert current is not None
        assert current.revision == 1
        assert sum(current.application_draft.values()) == 1

    asyncio.run(scenario())


def test_draft_change_invalidates_confirmation_for_previous_draft_revision():
    async def scenario():
        store = InMemorySessionStore()
        session = await store.create_session(application_draft={"name": "Example"})
        waiting = await store.create_pending_confirmation(
            session.session_id,
            expected_revision=0,
        )

        assert waiting.status == SessionStatus.AWAITING_CONFIRMATION
        assert waiting.pending_confirmation is not None
        assert waiting.pending_confirmation.draft_revision == waiting.draft_revision

        updated = await store.update_session(
            session.session_id,
            SessionUpdate(application_draft_patch={"name": "Updated example"}),
            expected_revision=waiting.revision,
        )

        assert updated.draft_revision == waiting.draft_revision + 1
        assert updated.pending_confirmation is None
        assert updated.status == SessionStatus.ACTIVE

    asyncio.run(scenario())


@pytest.mark.parametrize(
    "credential_key",
    [
        "password",
        "otp",
        "pin",
        "access_token",
        "authSecret",
        "api_key",
        "private_key",
        "passcode",
        "totp",
    ],
)
def test_application_draft_rejects_credential_fields_recursively(credential_key: str):
    async def scenario():
        store = InMemorySessionStore()
        with pytest.raises(ValueError, match="cannot contain credentials"):
            await store.create_session(
                application_draft={"nested": {credential_key: "not stored"}}
            )

    asyncio.run(scenario())


def test_expired_or_unknown_session_cannot_be_updated():
    async def scenario():
        clock = FakeClock()
        store = InMemorySessionStore(idle_timeout=timedelta(minutes=1), clock=clock)
        session = await store.create_session()
        clock.advance(timedelta(minutes=1))

        with pytest.raises(SessionNotFoundError):
            await store.update_session(
                session.session_id,
                SessionUpdate(workflow_step="review"),
                expected_revision=0,
            )
        assert await store.get_session(session.session_id) is None

    asyncio.run(scenario())
