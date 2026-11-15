"""Serializable models used by the in-memory session store."""

from __future__ import annotations

import copy
import math
import re
from collections.abc import Mapping
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


class SessionStatus(str, Enum):
    """Small set of workflow states used by the session store."""

    ACTIVE = "active"
    AWAITING_CONFIRMATION = "awaiting_confirmation"
    COMPLETED = "completed"
    CANCELLED = "cancelled"


class PendingConfirmation(BaseModel):
    """Confirmation request tied to one exact version of an application draft."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    confirmation_id: str
    draft_revision: int = Field(ge=0)
    created_at: datetime

    @field_validator("confirmation_id")
    @classmethod
    def confirmation_id_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("confirmation_id must not be blank")
        return value

    @field_validator("created_at")
    @classmethod
    def created_at_must_be_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamps must include a timezone")
        return value.astimezone(timezone.utc)


class SessionState(BaseModel):
    """A serializable snapshot of one user's in-memory workflow state."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    session_id: str
    workflow_step: str
    application_draft: dict[str, Any] = Field(default_factory=dict)
    status: SessionStatus = SessionStatus.ACTIVE
    created_at: datetime
    last_activity_at: datetime
    expires_at: datetime
    pending_confirmation: PendingConfirmation | None = None
    revision: int = Field(default=0, ge=0)
    draft_revision: int = Field(default=0, ge=0)

    @field_validator("session_id", "workflow_step")
    @classmethod
    def identifiers_and_step_must_not_be_blank(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("value must not be blank")
        return value

    @field_validator("created_at", "last_activity_at", "expires_at")
    @classmethod
    def timestamps_must_be_timezone_aware(cls, value: datetime) -> datetime:
        if value.tzinfo is None or value.utcoffset() is None:
            raise ValueError("timestamps must include a timezone")
        return value.astimezone(timezone.utc)

    @field_validator("application_draft", mode="before")
    @classmethod
    def validate_application_draft(cls, value: Any) -> dict[str, Any]:
        return validate_application_draft(value)

    @model_validator(mode="after")
    def confirmation_matches_current_draft(self) -> SessionState:
        if self.created_at > self.last_activity_at:
            raise ValueError("last_activity_at cannot precede created_at")
        if self.expires_at <= self.last_activity_at:
            raise ValueError("expires_at must be after last_activity_at")

        if self.status == SessionStatus.AWAITING_CONFIRMATION:
            if self.pending_confirmation is None:
                raise ValueError("awaiting_confirmation status needs a pending confirmation")
        elif self.pending_confirmation is not None:
            raise ValueError("pending confirmation requires awaiting_confirmation status")

        if (
            self.pending_confirmation is not None
            and self.pending_confirmation.draft_revision != self.draft_revision
        ):
            raise ValueError("pending confirmation must match the current draft revision")
        return self


class SessionUpdate(BaseModel):
    """A partial update; draft entries are merged into the existing draft."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    workflow_step: str | None = None
    application_draft_patch: dict[str, Any] | None = None
    status: SessionStatus | None = None

    @field_validator("workflow_step")
    @classmethod
    def workflow_step_must_not_be_blank(cls, value: str | None) -> str | None:
        if value is not None and not value.strip():
            raise ValueError("workflow_step must not be blank")
        return value

    @field_validator("application_draft_patch")
    @classmethod
    def validate_draft_patch(cls, value: dict[str, Any] | None) -> dict[str, Any] | None:
        if value is not None:
            return validate_application_draft(value)
        return value

    @model_validator(mode="after")
    def update_must_contain_changes(self) -> SessionUpdate:
        if not self.model_fields_set:
            raise ValueError("at least one update field is required")
        for field_name in self.model_fields_set:
            if getattr(self, field_name) is None:
                raise ValueError(f"{field_name} cannot be null in an update")
        if self.application_draft_patch == {}:
            raise ValueError("application_draft_patch cannot be empty")
        return self


_CREDENTIAL_KEY_TOKENS = {
    "auth",
    "authorization",
    "bearer",
    "credential",
    "credentials",
    "mfa",
    "mpin",
    "otp",
    "passcode",
    "passphrase",
    "password",
    "passwd",
    "pin",
    "private",
    "pwd",
    "secret",
    "token",
    "totp",
}
_CREDENTIAL_KEY_MARKERS = (
    "password",
    "passwd",
    "credential",
    "authorization",
    "bearer",
    "secret",
    "token",
    "apikey",
    "privatekey",
)


def _is_credential_key(key: str) -> bool:
    # Split camelCase and punctuation so names such as accessToken and
    # one_time_password are caught as well as plain password/otp keys.
    separated = re.sub(r"([a-z0-9])([A-Z])", r"\1_\2", key)
    tokens = set(re.findall(r"[a-z0-9]+", separated.casefold()))
    compact = "".join(tokens)
    if tokens & _CREDENTIAL_KEY_TOKENS:
        return True
    key_pairs = ({"api", "key"}, {"private", "key"}, {"client", "key"})
    if any(pair.issubset(tokens) for pair in key_pairs):
        return True
    return any(marker in compact for marker in _CREDENTIAL_KEY_MARKERS)


def validate_application_draft(value: Any) -> dict[str, Any]:
    """Copy a JSON-compatible draft and reject credential-like field names."""
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        raise ValueError("application_draft must be a mapping")

    draft = copy.deepcopy(dict(value))
    _validate_json_value(draft, set())
    return draft


def _validate_json_value(value: Any, ancestors: set[int]) -> None:
    if value is None or isinstance(value, (str, bool, int)):
        return
    if isinstance(value, float):
        if not math.isfinite(value):
            raise ValueError("application_draft must contain finite JSON numbers")
        return

    if isinstance(value, Mapping):
        identity = id(value)
        if identity in ancestors:
            raise ValueError("application_draft cannot contain circular data")
        ancestors.add(identity)
        try:
            for key, child in value.items():
                if not isinstance(key, str):
                    raise ValueError("application_draft keys must be strings")
                if _is_credential_key(key):
                    raise ValueError("application_draft cannot contain credentials")
                _validate_json_value(child, ancestors)
        finally:
            ancestors.remove(identity)
        return

    if isinstance(value, list):
        identity = id(value)
        if identity in ancestors:
            raise ValueError("application_draft cannot contain circular data")
        ancestors.add(identity)
        try:
            for child in value:
                _validate_json_value(child, ancestors)
        finally:
            ancestors.remove(identity)
        return

    raise ValueError("application_draft must contain JSON-compatible values")
