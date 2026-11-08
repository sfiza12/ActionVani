"""
ActionVani – Backend Health Tests
Member 3: Backend Foundation (Milestone 1)

These are automated tests that verify the two basic endpoints work correctly.

HOW TESTING WORKS:
  - pytest is a Python testing tool that finds and runs functions starting
    with `test_`.
  - FastAPI's TestClient lets you make fake HTTP requests to your app
    without actually starting a server. This makes tests fast and isolated.
  - Each `assert` statement checks that something is true. If it is false,
    the test fails and pytest shows you exactly what went wrong.

RUN THESE TESTS WITH:
  pytest tests/test_health.py -v
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app

# ---------------------------------------------------------------------------
# Create a test client
# ---------------------------------------------------------------------------
# TestClient wraps your FastAPI app and lets you send GET / POST / etc.
# requests inside a test without running a real server.
# ---------------------------------------------------------------------------
client = TestClient(app)


# ---------------------------------------------------------------------------
# Health endpoint tests
# ---------------------------------------------------------------------------

def test_health_returns_200():
    """GET /health must respond with HTTP 200 OK."""
    response = client.get("/health")
    assert response.status_code == 200, (
        f"Expected 200 but got {response.status_code}"
    )


def test_health_response_has_correct_keys():
    """GET /health response body must contain 'status' and 'message' keys."""
    response = client.get("/health")
    body = response.json()
    assert "status" in body, "Response is missing the 'status' field"
    assert "message" in body, "Response is missing the 'message' field"


def test_health_status_is_ok():
    """GET /health 'status' field must equal 'ok'."""
    response = client.get("/health")
    body = response.json()
    assert body["status"] == "ok", (
        f"Expected status='ok' but got status='{body['status']}'"
    )


def test_health_message_is_not_empty():
    """GET /health 'message' field must not be empty."""
    response = client.get("/health")
    body = response.json()
    assert body["message"], "The 'message' field should not be empty"


# ---------------------------------------------------------------------------
# Root endpoint tests
# ---------------------------------------------------------------------------

def test_root_returns_200():
    """GET / must respond with HTTP 200 OK."""
    response = client.get("/")
    assert response.status_code == 200, (
        f"Expected 200 but got {response.status_code}"
    )


def test_root_response_has_required_keys():
    """GET / response body must contain all expected information fields."""
    response = client.get("/")
    body = response.json()
    expected_keys = {"project", "description", "version", "status", "docs_url"}
    for key in expected_keys:
        assert key in body, f"Response is missing the '{key}' field"


def test_root_project_name():
    """GET / 'project' field must correctly identify ActionVani."""
    response = client.get("/")
    body = response.json()
    assert "ActionVani" in body["project"], (
        f"Expected 'ActionVani' in project name, got '{body['project']}'"
    )


def test_root_status_is_running():
    """GET / 'status' field must equal 'running'."""
    response = client.get("/")
    body = response.json()
    assert body["status"] == "running", (
        f"Expected status='running' but got status='{body['status']}'"
    )


def test_root_docs_url_is_present():
    """GET / 'docs_url' field must not be empty."""
    response = client.get("/")
    body = response.json()
    assert body["docs_url"], "The 'docs_url' field should not be empty"


# ---------------------------------------------------------------------------
# Negative / edge-case tests
# ---------------------------------------------------------------------------

def test_unknown_route_returns_404():
    """Requests to undefined routes must return HTTP 404 Not Found."""
    response = client.get("/nonexistent-endpoint")
    assert response.status_code == 404, (
        f"Expected 404 for unknown route but got {response.status_code}"
    )


def test_post_to_health_returns_405():
    """POST to /health (which only accepts GET) must return HTTP 405."""
    response = client.post("/health")
    assert response.status_code == 405, (
        f"Expected 405 Method Not Allowed but got {response.status_code}"
    )


def test_post_to_root_returns_405():
    """POST to / (which only accepts GET) must return HTTP 405."""
    response = client.post("/")
    assert response.status_code == 405, (
        f"Expected 405 Method Not Allowed but got {response.status_code}"
    )

