"""
ActionVani – FastAPI Backend
Member 3: Backend Foundation (Milestone 1)

This is the main entry point for the ActionVani backend server.
It currently exposes two simple HTTP endpoints:

  GET /         → General project information
  GET /health   → Health check to confirm the server is running

Future milestones will add:
  - WebSocket session management
  - Playwright browser automation
  - AI and speech processing integration
"""

from fastapi import FastAPI
from app.models import HealthResponse, InfoResponse

# ---------------------------------------------------------------------------
# App initialisation
# ---------------------------------------------------------------------------
# FastAPI() creates the web application object.
# Every endpoint (URL route) is registered on this object.
# ---------------------------------------------------------------------------
app = FastAPI(
    title="ActionVani Backend",
    description=(
        "Voice-driven agentic execution engine for Digital India public services. "
        "This backend orchestrates speech processing, AI reasoning, and "
        "browser automation to help citizens complete government portal applications."
    ),
    version="0.1.0",
)


# ---------------------------------------------------------------------------
# Root endpoint – GET /
# ---------------------------------------------------------------------------
# When someone visits http://localhost:8000/ this function runs.
# It returns a JSON response with basic project information.
# `response_model=InfoResponse` means FastAPI will validate the response
# against the InfoResponse Pydantic model before sending it.
# ---------------------------------------------------------------------------
@app.get("/", response_model=InfoResponse, tags=["General"])
def root() -> InfoResponse:
    """Return basic information about the ActionVani backend."""
    return InfoResponse(
        project="ActionVani (IndicAgent)",
        description=(
            "Voice-driven agentic execution engine for Digital India public services."
        ),
        version="0.1.0",
        status="running",
        docs_url="/docs",
    )


# ---------------------------------------------------------------------------
# Health endpoint – GET /health
# ---------------------------------------------------------------------------
# This endpoint is used to check that the server is alive.
# Automated tools, CI pipelines, and mobile clients can call this endpoint
# to confirm the backend is reachable before starting a session.
# ---------------------------------------------------------------------------
@app.get("/health", response_model=HealthResponse, tags=["Health"])
def health_check() -> HealthResponse:
    """Return the current health status of the backend server."""
    return HealthResponse(status="ok", message="ActionVani backend is running.")

