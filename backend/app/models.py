"""
ActionVani – Pydantic Response Models
Member 3: Backend Foundation (Milestone 1)

Pydantic models define the exact shape (structure) of JSON responses.

Why use Pydantic models?
  - FastAPI automatically validates that your response matches the model.
  - If you accidentally return a wrong field type, FastAPI catches it early.
  - The models are shown automatically in the /docs API documentation page.
  - They make it easy for other team members (Member 2 – Flutter client) to
    know exactly what JSON they will receive from each endpoint.
"""

from pydantic import BaseModel


class HealthResponse(BaseModel):
    """
    Response model for GET /health.

    Fields:
        status  – Always "ok" when the server is running.
        message – A human-readable message confirming the server state.
    """

    status: str
    message: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "status": "ok",
                "message": "ActionVani backend is running.",
            }
        }
    }


class InfoResponse(BaseModel):
    """
    Response model for GET /.

    Fields:
        project     – Full project name.
        description – Short one-line description of the project.
        version     – Current backend version string.
        status      – Server status (always "running" at this endpoint).
        docs_url    – URL where the auto-generated API docs can be found.
    """

    project: str
    description: str
    version: str
    status: str
    docs_url: str

    model_config = {
        "json_schema_extra": {
            "example": {
                "project": "ActionVani (IndicAgent)",
                "description": (
                    "Voice-driven agentic execution engine for "
                    "Digital India public services."
                ),
                "version": "0.1.0",
                "status": "running",
                "docs_url": "/docs",
            }
        }
    }

