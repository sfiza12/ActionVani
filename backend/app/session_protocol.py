"""Validation for the proposed ActionVani WebSocket message envelope."""

from typing import Any

from pydantic import BaseModel, ConfigDict, field_validator


class SessionEnvelope(BaseModel):
    """The four-field envelope requested for the initial WebSocket prototype.

    Event names are intentionally not constrained to a vocabulary while the
    client/backend contract is awaiting team confirmation.
    """

    model_config = ConfigDict(extra="forbid", strict=True)

    event: str
    session_id: str
    request_id: str
    data: Any

    @field_validator("event", "session_id", "request_id")
    @classmethod
    def require_nonblank_string(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("must not be blank")
        return value
