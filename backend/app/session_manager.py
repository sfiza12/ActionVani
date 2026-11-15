"""Stateless handling of individual ActionVani WebSocket connections."""

import json
from typing import Any

from fastapi import WebSocket, WebSocketDisconnect
from pydantic import ValidationError

from app.session_protocol import SessionEnvelope


def _reject_non_json_constant(value: str) -> None:
    """Reject JavaScript-style NaN/Infinity tokens, which are not JSON values."""
    raise ValueError(f"Invalid JSON constant: {value}")


class SessionManager:
    """Validate and echo envelopes without storing session state or payloads."""

    async def handle_connection(self, websocket: WebSocket) -> None:
        """Accept messages, echo valid envelopes, and close on invalid input.

        Invalid payloads use a provisional WebSocket policy-violation close
        (1008). The close reason is static so it cannot expose message contents.
        """
        await websocket.accept()

        while True:
            try:
                message = await websocket.receive()
            except WebSocketDisconnect:
                return

            if message.get("type") == "websocket.disconnect":
                return

            text = message.get("text")
            if not isinstance(text, str):
                await self._close_invalid(websocket)
                return

            try:
                payload: Any = json.loads(text, parse_constant=_reject_non_json_constant)
                envelope = SessionEnvelope.model_validate(payload)
            except (json.JSONDecodeError, ValueError, ValidationError, TypeError):
                await self._close_invalid(websocket)
                return

            await websocket.send_json(envelope.model_dump(mode="json"))

    @staticmethod
    async def _close_invalid(websocket: WebSocket) -> None:
        await websocket.close(code=1008, reason="Invalid session message.")
