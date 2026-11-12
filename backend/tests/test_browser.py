"""
ActionVani – Browser Automation & Security Tests
Member 3: Backend & Browser Automation

Automated tests for Playwright browser management, navigation, and security controls.
Tests run completely offline using local servers and test fixtures, with zero external dependencies.

Run these tests with:
    pytest tests/test_browser.py -v
"""

import http.server
from pathlib import Path
import threading
import time
from urllib.parse import urlparse
import pytest
from playwright.sync_api import Page, Route

from browser import (
    BrowserManager,
    BrowserManagerError,
    DEFAULT_ALLOWED_DOMAINS,
    DisallowedDomainError,
    DisallowedRedirectError,
    DisallowedSchemeError,
    NavigationManager,
    NavigationResult,
    SecurityError,
    SecurityPolicy,
)

# Path to the local test HTML form fixture
FIXTURE_FORM_PATH = Path(__file__).parent.parent / "test_form.html"


# ===========================================================================
# 1. Security Policy Unit Tests
# ===========================================================================

def test_security_policy_default_domains():
    """Verify default security policy includes essential local and gov domains."""
    policy = SecurityPolicy()
    assert "localhost" in policy.allowed_domains
    assert "127.0.0.1" in policy.allowed_domains
    assert "*.gov.in" in policy.allowed_domains
    assert "*.nic.in" in policy.allowed_domains


def test_security_policy_domain_matching():
    """Verify domain allowlist correctly matches exact and wildcard domains."""
    policy = SecurityPolicy(allowed_domains=["localhost", "*.gov.in", "example.com"])

    # Allowed domains
    assert policy.is_domain_allowed("localhost")
    assert policy.is_domain_allowed("services.india.gov.in")
    assert policy.is_domain_allowed("passport.gov.in")
    assert policy.is_domain_allowed("example.com")

    # Disallowed domains
    assert not policy.is_domain_allowed("malicious-site.com")
    assert not policy.is_domain_allowed("fakegov.in")  # Doesn't end in .gov.in
    assert not policy.is_domain_allowed("sub.example.com")  # No wildcard for example.com
    assert not policy.is_domain_allowed(None)
    assert not policy.is_domain_allowed("")


def test_security_policy_valid_http_url():
    """Validate approved http/https URLs pass validation."""
    policy = SecurityPolicy(allowed_domains=["*.gov.in"])
    url = "https://services.india.gov.in/service/search"
    assert policy.validate_url(url) == url


def test_security_policy_blocks_disallowed_domain():
    """Validate unapproved domain URLs raise DisallowedDomainError."""
    policy = SecurityPolicy(allowed_domains=["*.gov.in"])
    with pytest.raises(DisallowedDomainError) as exc_info:
        policy.validate_url("https://unapproved-portal.org/login")
    assert "unapproved-portal.org" in str(exc_info.value)


def test_security_policy_blocks_dangerous_schemes():
    """Validate javascript:, data:, and vbscript: schemes are blocked."""
    policy = SecurityPolicy()

    with pytest.raises(DisallowedSchemeError):
        policy.validate_url("javascript:alert(1)")

    with pytest.raises(DisallowedSchemeError):
        policy.validate_url("data:text/html;base64,PHNjcmlwdD5hbGVydCgxKTwvc2NyaXB0Pg==")

    with pytest.raises(DisallowedSchemeError):
        policy.validate_url("vbscript:msgbox(1)")


def test_security_policy_file_scheme_control():
    """Verify file:// scheme is DISABLED by default and must be explicitly enabled."""
    # 1. Default policy MUST block file:// URLs for production security
    default_policy = SecurityPolicy()
    assert default_policy.allow_file_scheme is False
    with pytest.raises(DisallowedSchemeError):
        default_policy.validate_url(FIXTURE_FORM_PATH.as_uri())

    # 2. Explicitly enabling file:// allows local testing fixtures
    test_policy = SecurityPolicy(allow_file_scheme=True)
    assert test_policy.allow_file_scheme is True
    assert test_policy.validate_url(FIXTURE_FORM_PATH.as_uri()) == FIXTURE_FORM_PATH.as_uri()


def test_security_policy_url_sanitization():
    """
    Verify sensitive parameters (passwords, tokens, Aadhaar, PAN, OTP, PIN)
    and Basic Auth netloc credentials are all redacted.
    """
    url = (
        "https://admin:SuperSecretPassword@services.gov.in/auth"
        "?token=abc123token"
        "&password=UserPassword99"
        "&aadhaar=123456789012"
        "&pan=ABCDE1234F"
        "&otp=987654"
        "&pin=4321"
        "&applicant_name=Priya"
        "&state=Delhi"
    )
    sanitized = SecurityPolicy.sanitize_url(url)

    # Sensitive values must be completely redacted
    assert "SuperSecretPassword" not in sanitized
    assert "abc123token" not in sanitized
    assert "UserPassword99" not in sanitized
    assert "123456789012" not in sanitized
    assert "ABCDE1234F" not in sanitized
    assert "987654" not in sanitized
    assert "4321" not in sanitized

    # Redacted markers must be present
    assert "[REDACTED]" in sanitized
    assert "admin:[REDACTED]@" in sanitized

    # Non-sensitive parameters must be preserved
    assert "applicant_name=Priya" in sanitized
    assert "state=Delhi" in sanitized


def test_navigation_result_sanitizes_errors_and_strings():
    """Verify NavigationResult string representations and error messages never expose credentials."""
    raw_error = "Failed connecting to https://portal.gov.in/login?password=my_pwd&token=sec_tok&aadhaar=999988887777"
    result = NavigationResult(
        success=False,
        requested_url="https://portal.gov.in/login?password=my_pwd&token=sec_tok&aadhaar=999988887777",
        error_message=raw_error,
    )

    # 1. Error message sanitized
    assert "my_pwd" not in (result.error_message or "")
    assert "sec_tok" not in (result.error_message or "")
    assert "999988887777" not in (result.error_message or "")

    # 2. str(result) and repr(result) sanitized
    str_repr = str(result)
    assert "my_pwd" not in str_repr
    assert "sec_tok" not in str_repr
    assert "999988887777" not in str_repr

    full_repr = repr(result)
    assert "my_pwd" not in full_repr
    assert "sec_tok" not in full_repr
    assert "999988887777" not in full_repr


# ===========================================================================
# 2. BrowserManager Lifecycle & Resource Cleanup Tests
# ===========================================================================

def test_browser_manager_launch_and_close():
    """Verify browser starts in headless mode and cleans up completely."""
    bm = BrowserManager(headless=True)
    assert not bm.is_running

    bm.start()
    assert bm.is_running

    page = bm.new_page()
    assert page is not None
    assert not page.is_closed()

    bm.close()
    assert not bm.is_running
    assert page.is_closed()


def test_browser_manager_context_manager():
    """Verify BrowserManager functions correctly as a Python context manager."""
    with BrowserManager(headless=True) as bm:
        assert bm.is_running
        page = bm.new_page()
        page.goto("about:blank")
        assert page.title() == ""

    # After exiting the with block, browser should be cleanly closed
    assert not bm.is_running


def test_browser_manager_multiple_close_is_safe():
    """Verify calling close() multiple times does not raise exceptions."""
    bm = BrowserManager(headless=True)
    bm.start()
    bm.close()
    # Second and third calls should be completely safe no-ops
    bm.close()
    bm.close()
    assert not bm.is_running


# ===========================================================================
# 3. Navigation & Redirect Security Tests
# ===========================================================================

def test_navigation_to_local_fixture_form():
    """Verify safe navigation to the local test form when file:// is explicitly enabled."""
    with BrowserManager(headless=True) as bm:
        page = bm.new_page()
        policy = SecurityPolicy(allow_file_scheme=True)
        nav = NavigationManager(security_policy=policy)

        result = nav.navigate(page, FIXTURE_FORM_PATH.as_uri())

        assert result.success is True
        assert result.error_message is None
        assert result.title == "ActionVani Test Form"
        assert result.final_url == FIXTURE_FORM_PATH.as_uri()


def test_navigation_to_local_fixture_form_blocked_by_default():
    """Verify navigation to file:// is blocked by default in production configuration."""
    with BrowserManager(headless=True) as bm:
        page = bm.new_page()
        # Default NavigationManager has allow_file_scheme=False
        nav = NavigationManager()

        result = nav.navigate(page, FIXTURE_FORM_PATH.as_uri())

        assert result.success is False
        assert "file://" in (result.error_message or "").lower()


def test_navigation_blocked_domain_before_network():
    """Verify navigating to an unapproved domain fails before any request is made."""
    with BrowserManager(headless=True) as bm:
        page = bm.new_page()
        policy = SecurityPolicy(allowed_domains=["*.gov.in"])
        nav = NavigationManager(security_policy=policy)

        result = nav.navigate(page, "https://malicious-bank.com/transfer")

        assert result.success is False
        assert "malicious-bank.com" in (result.error_message or "")
        # Ensure browser page was not navigated to the disallowed site
        assert page.url != "https://malicious-bank.com/transfer"


def test_navigation_redirect_to_disallowed_domain_blocked():
    """
    Verify that an approved starting URL cannot redirect to an unapproved domain.
    Ensures the request to the unauthorised destination is aborted BEFORE it is sent,
    and proves that the unauthorised destination receives ZERO requests.
    """
    unauthorised_requests = []

    class ApprovedHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            # Send HTTP 302 redirecting to the unauthorised destination
            self.send_response(302)
            self.send_header("Location", f"http://127.0.0.1:{unauthorised_port}/steal-data")
            self.end_headers()
        def log_message(self, *args): pass

    class UnauthorisedHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            unauthorised_requests.append(self.path)
            self.send_response(200)
            self.end_headers()
            self.wfile.write(b"unauthorised content")
        def log_message(self, *args): pass

    # Setup approved server on localhost
    approved_server = http.server.HTTPServer(("localhost", 0), ApprovedHandler)
    approved_port = approved_server.server_port
    threading.Thread(target=approved_server.serve_forever, daemon=True).start()

    # Setup unauthorised server on 127.0.0.1
    unauthorised_server = http.server.HTTPServer(("127.0.0.1", 0), UnauthorisedHandler)
    unauthorised_port = unauthorised_server.server_port
    threading.Thread(target=unauthorised_server.serve_forever, daemon=True).start()

    try:
        with BrowserManager(headless=True) as bm:
            page = bm.new_page()

            # Allow 'localhost', but explicitly NOT '127.0.0.1'
            policy = SecurityPolicy(allowed_domains=["localhost"])
            nav = NavigationManager(security_policy=policy)

            result = nav.navigate(page, f"http://localhost:{approved_port}/safe-portal")

            # 1. Navigation must fail
            assert result.success is False
            assert "Redirect blocked" in (result.error_message or "") or "not in allowlist" in (result.error_message or "")

            # 2. CRITICAL: The unauthorised destination received ZERO requests
            assert len(unauthorised_requests) == 0, (
                f"Security breach: Unauthorised destination received requests: {unauthorised_requests}"
            )

            # 3. Page did not land on the unauthorised location
            assert "steal-data" not in page.url
    finally:
        approved_server.shutdown()
        unauthorised_server.shutdown()


def test_navigation_timeout_handling():
    """Verify slow/hanging pages fail gracefully on timeout without crashing."""
    class SlowHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            time.sleep(2)
            self.send_response(200)
            self.end_headers()
        def log_message(self, *args): pass

    slow_server = http.server.HTTPServer(("127.0.0.1", 0), SlowHandler)
    slow_port = slow_server.server_port
    threading.Thread(target=slow_server.serve_forever, daemon=True).start()

    try:
        with BrowserManager(headless=True) as bm:
            page = bm.new_page()
            nav = NavigationManager(default_timeout_ms=500)

            result = nav.navigate(page, f"http://127.0.0.1:{slow_port}/slow-portal", timeout_ms=500)

            assert result.success is False
            assert "timed out" in (result.error_message or "").lower()
    finally:
        slow_server.shutdown()
