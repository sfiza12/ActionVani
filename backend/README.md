# ActionVani Backend

Member 3's Python backend foundation for ActionVani (IndicAgent). The current code includes FastAPI health endpoints, a minimal WebSocket envelope-validation/echo prototype, and a reusable Playwright browser workflow. This repository is still under development and is not production-ready.

## Current structure

```text
backend/
├── app/
│   ├── __init__.py             Python package marker
│   ├── main.py                  FastAPI HTTP app and router registration
│   ├── models.py                HTTP response models
│   ├── session_protocol.py      Proposed WebSocket envelope validation
│   ├── session_manager.py       Stateless connection validation and echo
│   └── websocket.py             /ws/session route
├── browser/
│   ├── __init__.py              Browser automation package exports
│   ├── browser_manager.py       Chromium lifecycle, isolated contexts, page creation
│   ├── navigation.py            URL navigation, redirect checks, structured results
│   ├── security.py              URL scheme/domain policy and URL sanitization
│   ├── dom_extractor.py         Safe form-control metadata extraction
│   ├── form_filler.py           Supported field filling and verification
│   └── validator.py             Required/native validity and requested-value checks
├── tests/
│   ├── test_health.py
│   ├── test_browser.py
│   ├── test_form_automation.py
│   └── test_websocket.py        Offline WebSocket contract tests
├── test_form.html                Offline browser test fixture
├── requirements.txt
└── README.md
```

The HTTP API exposes `GET /` and `GET /health`. The WebSocket prototype is at `/ws/session`; it does not manage persistent sessions or invoke browser automation or AI. Browser automation remains a separate Python module and is not wired to a service endpoint or mobile session workflow.

## Setup and tests

From the repository's `backend/` directory in PowerShell:

```powershell
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
.\.venv\Scripts\python.exe -m playwright install chromium
.\.venv\Scripts\python.exe -m pytest tests/ -v
```

The tests use the local HTML fixture and local HTTP servers; they do not navigate to external government sites. Playwright's Chromium binary must be installed before running the browser tests. The project pins FastAPI, Pydantic, Playwright, pytest, and httpx in `requirements.txt`.

Start the current FastAPI foundation from `backend/` with:

```powershell
.\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

The root endpoint is `http://localhost:8000/`, health check is `http://localhost:8000/health`, and the generated API docs are at `http://localhost:8000/docs`.

## WebSocket prototype

`app.websocket` registers `WS /ws/session`. `SessionManager.handle_connection(websocket)` accepts JSON text messages, validates each message with `SessionEnvelope`, and echoes valid envelopes to the same connection. It keeps no session registry or message history and does not call an AI adapter or browser module. Client disconnects end the handler. Malformed JSON, invalid envelopes, and non-text frames close the connection with WebSocket code `1008` and a static reason.

The prototype validates this required envelope shape:

```json
{
  "event": "example.event",
  "session_id": "session-123",
  "request_id": "request-456",
  "data": {"message": "example"}
}
```

All four keys are required; extra keys are rejected. `event`, `session_id`, and `request_id` must be nonblank strings. `data` may be any JSON value. The event string is passed through as an opaque value: event names and their directions are proposed and still require agreement with Member 2 and the team. The example event name above is illustrative, not a confirmed contract. Session ownership/lifecycle, request correlation, invalid-message policy, authentication, origin checks, and message size/rate limits also need team and security review before client integration or deployment. Do not send credentials or sensitive citizen data through this echo prototype; it is not an authenticated or hardened data channel.

The endpoint is intentionally independent of AI interfaces. `SessionManager` is a connection boundary that can be extended after Member 4 confirms the adapter contract; this implementation does not define that interface. It does not stream audio, perform form-state synchronization, map voice commands to actions, or submit portal forms.

## Browser modules

### Browser lifecycle: `BrowserManager`

`BrowserManager(headless=True, slow_mo=0, default_timeout_ms=30000)` owns the Playwright and Chromium lifecycle. Its public methods are `start()`, `new_context(**kwargs)`, `new_page(context=None)`, and `close()`. It can also be used as a context manager, which starts the browser on entry and closes its pages, contexts, and browser on exit. `is_running` reports whether the browser is active.

### Navigation and URL security: `NavigationManager` and `SecurityPolicy`

`NavigationManager(security_policy=None, default_timeout_ms=30000).navigate(page, url, timeout_ms=None, wait_until="domcontentloaded")` validates the target before navigation, inspects redirected requests, and returns a `NavigationResult` with success, URL, status, title, redirect, or sanitized error information.

`SecurityPolicy(allowed_domains=None, allow_file_scheme=False)` provides `validate_url(url)`, `is_domain_allowed(hostname)`, `add_allowed_domain(domain)`, and `remove_allowed_domain(domain)`. It also provides `sanitize_url(url)` and `sanitize_text(text)` for masking known sensitive URL parameters and credentials. Its defaults allow localhost addresses and `gov.in`/`nic.in` domains. `file://` is disabled unless explicitly enabled for local fixtures.

The allowlist and redirect checks limit navigation destinations; they do not prove that a portal is authentic, safe, or compliant with its own rules. Use a deliberately configured allowlist for the deployment environment. URL sanitization covers known URL patterns; it is not a substitute for careful handling of citizen data throughout an application.

### Form metadata: `DOMExtractor`

Create it with a Playwright page and call `DOMExtractor(page).extract_fields()`. It returns structured metadata for supported native `input`, `select`, and `textarea` controls: ID, name, type, associated label when available, placeholder, required/disabled/read-only flags, selector, and dropdown options. Select metadata also identifies multi-selects and disabled options. Hidden inputs and button-like input types are omitted. Current control values are not returned.

### Filling: `FormFiller`

Call `FormFiller(page).fill_fields(fields, values)`, where `fields` comes from `DOMExtractor` and `values` is keyed by a field's name, ID, or label. It supports text inputs, date inputs, textareas, single-select dropdowns, and checkboxes (checkbox values must be booleans). Dropdown choices can be matched by option value or visible label. Each result includes a status and a verification flag, without echoing the requested or actual field value.

Disabled and read-only fields are reported without being changed. Unsupported controls include password, file, radio, other input types, and multi-select dropdowns. A disabled dropdown choice receives a distinct `disabled_option` status. The filler never clicks a submit button.

### Validation: `FormValidator`

Call `FormValidator(page).validate(fields, requested_values=None)`. The structured result includes per-field inspection status, required-field status, native HTML validity, browser validation messages, and requested-value match status when applicable. Required radio-button groups can be validated as groups. Radio-button filling and requested-option matching are not currently supported.

Native HTML validation only checks browser-level constraints such as `required`, type, and declared limits. It does not verify government-specific business rules or establish that an application is complete or eligible.

## Example workflow

```python
from browser import (
    BrowserManager,
    DOMExtractor,
    FormFiller,
    FormValidator,
    NavigationManager,
)

approved_url = "https://your-approved-portal.gov.in/application"
requested_values = {
    "name": "Asha Rao",
    "dob": "2002-04-23",
    "gender": "female",
    "agreement": True,
}

with BrowserManager(headless=True) as manager:
    page = manager.new_page()
    navigation = NavigationManager()
    nav_result = navigation.navigate(page, approved_url)

    if nav_result.success:
        fields = DOMExtractor(page).extract_fields()
        fill_result = FormFiller(page).fill_fields(fields, requested_values)
        validation_result = FormValidator(page).validate(fields, requested_values)
        # Present the proposed application details and wait for explicit user
        # confirmation before any final submission workflow.
```

For local fixture testing only, create `SecurityPolicy(allow_file_scheme=True)` and pass it to `NavigationManager`. Do not enable `file://` for normal portal navigation.

## Security and current limitations

- Do not log or unnecessarily persist passwords, Aadhaar, PAN, OTPs, or other citizen data. The form modules avoid returning live field values in extracted metadata and result messages, but callers still handle the supplied values and must protect them.
- Do not bypass CAPTCHA or OTP checks. CAPTCHA/OTP handling is not implemented.
- Do not automatically submit an application. A final submission must require explicit user confirmation in the integrating application; the current `FormFiller` has no submit action.
- The WebSocket endpoint currently has no authentication, origin policy, persistent session lifecycle, message-size/rate limits, or transport-to-AI adapter. It echoes a valid envelope's data to the originating connection; use only nonsensitive sample data until the protocol and security controls are agreed and implemented.
- Form support is limited to the controls listed above. Custom widgets and unsupported native control types require further implementation.
- Browser validity does not guarantee portal-specific business-rule compliance.
- This milestone is not a production deployment package. Authentication, session orchestration, data-retention policy, monitoring, and operational hardening require separate design and review.
