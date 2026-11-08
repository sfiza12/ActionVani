# ActionVani – Backend Developer Guide

This folder contains the **Python FastAPI backend** for ActionVani (IndicAgent).

The backend is responsible for orchestrating WebSocket communication,
AI reasoning, and browser automation. This document explains how to set up,
run, and test it on your local machine.

---

## Folder Structure

```
backend/
├── app/
│   ├── __init__.py    ← Marks folder as a Python package
│   ├── main.py        ← FastAPI app + all HTTP endpoints
│   └── models.py      ← Pydantic response models
├── browser/           ← Playwright automation (future milestone)
├── ai/                ← AI, speech, and OCR logic (future milestone)
├── tests/
│   ├── __init__.py
│   └── test_health.py ← Automated pytest tests for Milestone 1
├── requirements.txt   ← All Python dependencies
└── README.md          ← This file
```

---

## Prerequisites

- **Python 3.10 or later** must be installed.  
  Check your version: `python --version`
- **pip** must be available.  
  Check: `pip --version`

---

## Step 1 – Create a Virtual Environment

A virtual environment is an isolated space where Python packages are installed
only for this project. This avoids conflicts with system-wide packages.

**Windows (PowerShell):**
```powershell
cd backend
python -m venv .venv
```

**macOS / Linux:**
```bash
cd backend
python3 -m venv .venv
```

> The `.venv` folder is created inside `backend/`. It is already listed in
> the root `.gitignore` so it will not be committed to Git.

---

## Step 2 – Activate the Virtual Environment

You must activate the virtual environment every time you open a new terminal.

**Windows (PowerShell):**
```powershell
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks the script, run this once to allow it:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**macOS / Linux:**
```bash
source .venv/bin/activate
```

When activated, your terminal prompt will start with `(.venv)`.

---

## Step 3 – Install Dependencies

With the virtual environment active:

```bash
pip install -r requirements.txt
```

This installs:

| Package              | Purpose                                             |
|----------------------|-----------------------------------------------------|
| `fastapi`            | Web framework for building the API                  |
| `uvicorn[standard]`  | ASGI server that runs the FastAPI application       |
| `pydantic`           | Data validation for request and response models     |
| `pytest`             | Testing framework                                   |
| `httpx`              | HTTP client used by FastAPI's TestClient            |

---

## Step 4 – Start the Backend Server

From the `backend/` folder (with the virtual environment active):

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

**What each part means:**

| Part                  | Meaning                                                        |
|-----------------------|----------------------------------------------------------------|
| `app.main`            | The Python module path: `app/` folder → `main.py` file        |
| `:app`                | The FastAPI application object named `app` inside `main.py`    |
| `--host 0.0.0.0`      | Accept connections from any network interface                  |
| `--port 8000`         | Listen on port 8000                                            |
| `--reload`            | Automatically restart the server when code changes (dev mode)  |

Once started, you can open these URLs in your browser:

| URL                              | Description                              |
|----------------------------------|------------------------------------------|
| `http://localhost:8000/`         | Root endpoint – project information      |
| `http://localhost:8000/health`   | Health check endpoint                    |
| `http://localhost:8000/docs`     | Interactive API documentation (Swagger)  |
| `http://localhost:8000/redoc`    | Alternative API documentation (ReDoc)    |

---

## Step 5 – Run the Tests

Stop the server first (press `Ctrl + C`), then from the `backend/` folder:

```bash
pytest tests/test_health.py -v
```

The `-v` flag (verbose) shows each test name and whether it passed or failed.

**Expected output:**
```
tests/test_health.py::test_health_returns_200              PASSED
tests/test_health.py::test_health_response_has_correct_keys PASSED
tests/test_health.py::test_health_status_is_ok             PASSED
tests/test_health.py::test_health_message_is_not_empty     PASSED
tests/test_health.py::test_root_returns_200                PASSED
tests/test_health.py::test_root_response_has_required_keys PASSED
tests/test_health.py::test_root_project_name               PASSED
tests/test_health.py::test_root_status_is_running          PASSED
tests/test_health.py::test_root_docs_url_is_present        PASSED
tests/test_health.py::test_unknown_route_returns_404       PASSED
tests/test_health.py::test_post_to_health_returns_405      PASSED
tests/test_health.py::test_post_to_root_returns_405        PASSED

12 passed
```

---

## Available Endpoints

### `GET /`

Returns basic project information.

**Example response:**
```json
{
  "project": "ActionVani (IndicAgent)",
  "description": "Voice-driven agentic execution engine for Digital India public services.",
  "version": "0.1.0",
  "status": "running",
  "docs_url": "/docs"
}
```

---

### `GET /health`

Returns the health status of the backend server.

**Example response:**
```json
{
  "status": "ok",
  "message": "ActionVani backend is running."
}
```

---

## Deactivating the Virtual Environment

When you are done working, deactivate the environment:

```bash
deactivate
```

---

## Next Milestones

Future backend milestones will add:

- WebSocket session management (real-time communication with the Flutter app).
- Playwright browser automation for government portal navigation.
- AI and speech processing integration.

