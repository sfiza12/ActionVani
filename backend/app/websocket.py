"""WebSocket routes for the ActionVani backend."""

from fastapi import APIRouter, WebSocket

from app.session_manager import SessionManager

router = APIRouter(tags=["WebSocket"])
session_manager = SessionManager()


@router.websocket("/ws/session")
async def session_socket(websocket: WebSocket) -> None:
    """Validate and echo proposed session envelopes over one connection."""
    await session_manager.handle_connection(websocket)
