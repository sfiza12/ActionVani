"""Offline tests for the minimal /ws/session envelope echo prototype."""

import pytest
from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect

from app.main import app

client = TestClient(app)


def test_valid_envelope_is_echoed_without_interpreting_proposed_event_name():
    envelope = {
        "event": "example.event",
        "session_id": "session-123",
        "request_id": "request-456",
        "data": {"message": "hello", "items": [1, True, None]},
    }

    with client.websocket_connect("/ws/session") as websocket:
        websocket.send_json(envelope)
        assert websocket.receive_json() == envelope


@pytest.mark.parametrize(
    "raw_message",
    [
        "{not-json",
        '{"event":"example.event","session_id":"s1","request_id":"r1"}',
        '{"event":"example.event","session_id":"s1","request_id":"r1","data":null,"extra":true}',
        '{"event":"  ","session_id":"s1","request_id":"r1","data":null}',
    ],
    ids=["malformed-json", "missing-data", "unexpected-field", "blank-event"],
)
def test_invalid_message_closes_connection_with_policy_violation(raw_message: str):
    with client.websocket_connect("/ws/session") as websocket:
        websocket.send_text(raw_message)
        with pytest.raises(WebSocketDisconnect) as error:
            websocket.receive_json()

    assert error.value.code == 1008


def test_client_disconnection_is_handled_without_server_error():
    with client.websocket_connect("/ws/session") as websocket:
        websocket.close(code=1000)
