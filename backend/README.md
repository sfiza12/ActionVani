# ActionVani Backend

Member 3's Python backend foundation for ActionVani (IndicAgent). The current code includes FastAPI health endpoints and a reusable Playwright browser workflow. This repository is still under development; this README does not describe it as production-ready.

## Current structure

```text
backend/
├── app/                         FastAPI application and response models
├── browser/
│   ├── browser_manager.py       Chromium lifecycle, isolated contexts, page creation
│   ├── navigation.py            URL navigation, redirect checks, structured results
│   ├── security.py              URL scheme/domain policy and URL sanitization
│   ├── dom_extractor.py         Safe form-control metadata extraction
│   ├── form_filler.py           Supported field filling and verification
│   └── validator.py             Required/native validity and requested-value checks
├── tests/
│   ├── test_health.py
│   ├── test_browser.py
│   └── test_form_automation.py
├── test_form.html                Offline browser test fixture
├── requirements.txt
└── README.md
```

The HTTP API currently exposes `GET /` and `GET /health`. Browser automation is a Python module and is not yet wired into a service endpoint or mobile session workflow.

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
- Form support is limited to the controls listed above. Custom widgets and unsupported native control types require further implementation.
- Browser validity does not guarantee portal-specific business-rule compliance.
- This milestone is not a production deployment package. Authentication, session orchestration, data-retention policy, monitoring, and operational hardening require separate design and review.