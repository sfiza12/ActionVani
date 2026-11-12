# ActionVani – Backend Developer Guide

This folder contains the **Python FastAPI backend** and **Playwright Browser Automation Foundation** for ActionVani (IndicAgent).

The backend is responsible for orchestrating WebSocket communication, AI reasoning, and secure browser automation for public service portals. This document explains how to set up, run, and test it on your local machine.

---

## Folder Structure

```
backend/
├── app/
│   ├── __init__.py        ← Marks folder as a Python package
│   ├── main.py            ← FastAPI app + HTTP endpoints (GET /, GET /health)
│   └── models.py          ← Pydantic response models
├── browser/               ← Playwright automation foundation
│   ├── __init__.py        ← Package exports (BrowserManager, NavigationManager, etc.)
│   ├── browser_manager.py ← Safe Chromium lifecycle (launch, context/page creation, cleanup)
│   ├── navigation.py      ← Safe page navigation, timeouts, and redirect enforcement
│   └── security.py        ← Configurable domain allowlist & URL sanitization
├── ai/                    ← AI, speech, and OCR logic (future milestone)
├── tests/
│   ├── __init__.py
│   ├── test_health.py     ← Automated tests for FastAPI foundation (12 tests)
│   └── test_browser.py    ← Automated tests for Browser & Security modules (14 tests)
├── test_form.html         ← Local test form fixture for offline testing
├── requirements.txt       ← All Python dependencies (pinned)
└── README.md              ← This developer guide
```

---

## Prerequisites

- **Python 3.10 or later** must be installed.  
  Check version: `python --version`
- **pip** must be available.  
  Check: `pip --version`

---

## Step 1 – Create and Activate Virtual Environment

**Windows (PowerShell):**
```powershell
cd backend
python -m venv .venv
.\.venv\Scripts\Activate.ps1
```

If PowerShell blocks the activation script, run this once:
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
```

**macOS / Linux:**
```bash
cd backend
python3 -m venv .venv
source .venv/bin/activate
```

---

## Step 2 – Install Dependencies

With `.venv` activated:

```bash
pip install -r requirements.txt
```

This installs:

| Package              | Purpose                                             |
|----------------------|-----------------------------------------------------|
| `fastapi`            | Web framework for building the API                  |
| `uvicorn[standard]`  | ASGI server that runs the FastAPI application       |
| `pydantic`           | Data validation for request and response models     |
| `playwright`         | Headed & headless Chromium browser automation       |
| `pytest`             | Testing framework                                   |
| `httpx`              | HTTP client used by FastAPI's TestClient            |

---

## Step 3 – Install Playwright Chromium

Playwright needs the Chromium browser binary to drive web sessions. Install Chromium once:

```bash
playwright install chromium
```

---

## Step 4 – Browser Module Architecture & Security

The browser module (`backend/browser/`) converts earlier experimental automation into modular, secure, production-grade components:

### 1. `BrowserManager` (`browser/browser_manager.py`)
- Launches Chromium using Playwright in either `headless=True` (automated) or `headless=False` (visual debugging) mode.
- Creates isolated contexts (`new_context()`) and tabs (`new_page()`).
- Implements Python context manager support (`with BrowserManager() as bm:`).
- Guarantees complete cleanup on error or exit so orphan browser processes are never left running.

### 2. `NavigationManager` (`browser/navigation.py`)
- Manages safe navigation to approved web addresses.
- Intercepts and validates HTTP redirect targets (e.g. 301, 302, 307) so an approved URL cannot secretly redirect to an untrusted domain.
- Handles timeouts and network drops gracefully without crashing, returning structured `NavigationResult` objects.

### 3. `SecurityPolicy` (`browser/security.py`)
- **Configurable Allowlist**: By default allows `localhost`, `127.0.0.1`, and official Indian public service domains (`*.gov.in`, `*.nic.in`).
- **Scheme Enforcement**: Only `http`, `https`, and (when enabled for testing) `file://` are permitted. Dangerous schemes like `javascript:`, `data:`, and `vbscript:` are blocked.
- **Sensitive Data Masking**: Automatically redacts sensitive query parameters (such as `token`, `password`, `key`, `aadhaar`, `otp`) from logs and error messages.

---

## Step 5 – Running Automated Tests

ActionVani backend includes comprehensive automated tests that run 100% offline without hitting external websites.

From the `backend/` directory:

### Run all tests:
```bash
pytest tests/ -v
```

### Run only FastAPI health tests:
```bash
pytest tests/test_health.py -v
```

### Run only Browser & Security tests:
```bash
pytest tests/test_browser.py -v
```

**Expected output summary:**
```
tests/test_browser.py::test_security_policy_default_domains PASSED
tests/test_browser.py::test_security_policy_domain_matching PASSED
tests/test_browser.py::test_security_policy_valid_http_url PASSED
tests/test_browser.py::test_security_policy_blocks_disallowed_domain PASSED
tests/test_browser.py::test_security_policy_blocks_dangerous_schemes PASSED
tests/test_browser.py::test_security_policy_file_scheme_control PASSED
tests/test_browser.py::test_security_policy_url_sanitization PASSED
tests/test_browser.py::test_browser_manager_launch_and_close PASSED
tests/test_browser.py::test_browser_manager_context_manager PASSED
tests/test_browser.py::test_browser_manager_multiple_close_is_safe PASSED
tests/test_browser.py::test_navigation_to_local_fixture_form PASSED
tests/test_browser.py::test_navigation_blocked_domain_before_network PASSED
tests/test_browser.py::test_navigation_redirect_to_disallowed_domain_blocked PASSED
tests/test_browser.py::test_navigation_timeout_handling PASSED
tests/test_health.py::test_health_returns_200 PASSED
...
26 passed in 5.5s
```

---

## Step 6 – Start the Backend Server

From the `backend/` folder:

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

URLs:
- Root info: `http://localhost:8000/`
- Health check: `http://localhost:8000/health`
- Swagger documentation: `http://localhost:8000/docs`

---

## Next Steps

- Form element extraction & state synchronization module.
- Voice-to-Action mapping.
- WebSocket session manager for real-time Flutter mobile app integration.
