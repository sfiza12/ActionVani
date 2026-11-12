"""
ActionVani – Browser Navigation Controller
Member 3: Backend & Browser Automation

This module handles safe and robust page navigation for Playwright browser automation.

Key Responsibilities:
  - Validates destination URLs against the SecurityPolicy before navigation.
  - Intercepts requests and HTTP redirects via Playwright request routing so that
    requests to unauthorised destinations are aborted BEFORE they are sent.
  - Sanitises URLs in NavigationResult errors, logs, and string representations
    to prevent exposure of passwords, tokens, Aadhaar, PAN, and OTP values.
  - Gracefully handles network errors, timeouts, and navigation aborts.
  - Returns structured, strongly-typed NavigationResult objects.
"""

import logging
from dataclasses import dataclass
from typing import Optional
from urllib.parse import urljoin, urlparse

from playwright.sync_api import (
    Error as PlaywrightError,
    Page,
    Response,
    Route,
    TimeoutError as PlaywrightTimeoutError,
)

from browser.security import (
    DisallowedDomainError,
    DisallowedRedirectError,
    DisallowedSchemeError,
    SecurityError,
    SecurityPolicy,
)

logger = logging.getLogger("actionvani.navigation")


@dataclass
class NavigationResult:
    """
    Structured outcome of a navigation attempt.

    Fields:
        success: Whether the page successfully loaded.
        requested_url: The initial URL requested by the caller.
        final_url: The actual URL after any redirects.
        status_code: HTTP response status code (if available, e.g. 200, 404).
        title: Page title after loading.
        error_message: Sanitized human-readable error description if navigation failed.
        redirected: Whether the request underwent any redirection.
    """

    success: bool
    requested_url: str
    final_url: Optional[str] = None
    status_code: Optional[int] = None
    title: Optional[str] = None
    error_message: Optional[str] = None
    redirected: bool = False

    def __post_init__(self) -> None:
        """Ensure any error message has embedded credentials and tokens sanitized."""
        if self.error_message:
            self.error_message = SecurityPolicy.sanitize_text(self.error_message)

    @property
    def sanitized_requested_url(self) -> str:
        """Return the requested URL with any sensitive query values redacted."""
        return SecurityPolicy.sanitize_url(self.requested_url)

    @property
    def sanitized_final_url(self) -> Optional[str]:
        """Return the final destination URL with any sensitive query values redacted."""
        return SecurityPolicy.sanitize_url(self.final_url) if self.final_url else None

    def __str__(self) -> str:
        req = self.sanitized_requested_url
        if self.success:
            return f"<NavigationResult success=True url='{req}' status={self.status_code}>"
        return f"<NavigationResult success=False url='{req}' error='{self.error_message}'>"

    def __repr__(self) -> str:
        req = self.sanitized_requested_url
        fin = self.sanitized_final_url
        return (
            f"NavigationResult(success={self.success}, requested_url='{req}', "
            f"final_url='{fin}', status_code={self.status_code}, "
            f"title={repr(self.title)}, error_message={repr(self.error_message)}, "
            f"redirected={self.redirected})"
        )


class NavigationManager:
    """
    Orchestrates safe browser navigation.

    Example:
        ```python
        nav = NavigationManager()
        result = nav.navigate(page, "https://services.india.gov.in")
        if result.success:
            print("Loaded page:", result.title)
        else:
            print("Navigation failed:", result.error_message)
        ```
    """

    def __init__(
        self,
        security_policy: Optional[SecurityPolicy] = None,
        default_timeout_ms: int = 30000,
    ) -> None:
        """
        Initialize the navigation controller.

        Args:
            security_policy: Optional custom SecurityPolicy. Uses default allowlist if None.
            default_timeout_ms: Maximum time in ms to wait for page load (default: 30s).
        """
        self.security_policy: SecurityPolicy = security_policy or SecurityPolicy()
        self.default_timeout_ms: int = default_timeout_ms

    def navigate(
        self,
        page: Page,
        url: str,
        timeout_ms: Optional[int] = None,
        wait_until: str = "domcontentloaded",
    ) -> NavigationResult:
        """
        Navigate a page to the target URL with strict security and redirect checks.

        Args:
            page: Playwright Page object to navigate.
            url: The destination web address.
            timeout_ms: Milliseconds before navigation times out. Defaults to self.default_timeout_ms.
            wait_until: When to consider navigation succeeded ('domcontentloaded', 'load', 'networkidle').

        Returns:
            NavigationResult describing the outcome.
        """
        timeout = timeout_ms if timeout_ms is not None else self.default_timeout_ms
        sanitized_target = SecurityPolicy.sanitize_url(url)

        # 1. Pre-navigation Security Validation (before touching network or browser)
        try:
            self.security_policy.validate_url(url)
        except SecurityError as sec_err:
            logger.warning(
                "Security policy rejected navigation to %s: %s",
                sanitized_target,
                sec_err,
            )
            return NavigationResult(
                success=False,
                requested_url=url,
                error_message=SecurityPolicy.sanitize_text(str(sec_err)),
            )

        # 2. Setup Request Routing & Interception
        # We intercept all requests and use route.fetch(max_redirects=0) so that
        # requests to unauthorised redirect destinations are aborted BEFORE they are sent.
        disallowed_redirect_detected = False
        redirect_blocked_reason = ""

        def handle_route(route: Route) -> None:
            nonlocal disallowed_redirect_detected, redirect_blocked_reason
            req_url = route.request.url

            # Allow local file:// URLs only if explicitly enabled
            if req_url.startswith("file:"):
                if not self.security_policy.allow_file_scheme:
                    disallowed_redirect_detected = True
                    redirect_blocked_reason = (
                        "Navigation blocked: Local file:// scheme is disabled."
                    )
                    logger.warning(redirect_blocked_reason)
                    route.abort("accessdenied")
                    return
                route.continue_()
                return

            if req_url.startswith("about:"):
                route.continue_()
                return

            parsed = urlparse(req_url)
            scheme = (parsed.scheme or "").lower()

            if scheme not in ("http", "https"):
                disallowed_redirect_detected = True
                redirect_blocked_reason = f"Navigation blocked: Forbidden scheme '{scheme}'."
                logger.warning(redirect_blocked_reason)
                route.abort("accessdenied")
                return

            # A. Check destination domain BEFORE any request is sent
            if not self.security_policy.is_domain_allowed(parsed.hostname):
                disallowed_redirect_detected = True
                redirect_blocked_reason = (
                    f"Navigation blocked: Destination domain '{parsed.hostname}' is not in allowlist."
                )
                logger.warning(
                    "Blocked request before sending to unauthorised domain: %s",
                    SecurityPolicy.sanitize_url(req_url),
                )
                route.abort("accessdenied")
                return

            # B. Fetch with max_redirects=0 to intercept redirect responses BEFORE following them
            try:
                response = route.fetch(timeout=timeout, max_redirects=0)
            except Exception as exc:
                logger.debug(
                    "Route fetch encountered error for %s: %s",
                    SecurityPolicy.sanitize_url(req_url),
                    exc,
                )
                route.abort("failed")
                return

            # C. Check if the response is an HTTP redirect (301, 302, 303, 307, 308)
            if response.status in (301, 302, 303, 307, 308):
                location = response.headers.get("location") or ""
                if location:
                    target_url = urljoin(req_url, location)
                    target_parsed = urlparse(target_url)
                    target_scheme = (target_parsed.scheme or "").lower()

                    if target_scheme in ("http", "https"):
                        if not self.security_policy.is_domain_allowed(target_parsed.hostname):
                            disallowed_redirect_detected = True
                            redirect_blocked_reason = (
                                f"Redirect blocked: Destination domain '{target_parsed.hostname}' is not in allowlist."
                            )
                            logger.warning(
                                "Aborted redirect before request sent: %s -> %s",
                                SecurityPolicy.sanitize_url(req_url),
                                SecurityPolicy.sanitize_url(target_url),
                            )
                            # Abort right here! The unauthorised destination NEVER receives a request!
                            route.abort("accessdenied")
                            return
                    elif target_scheme == "file":
                        if not self.security_policy.allow_file_scheme:
                            disallowed_redirect_detected = True
                            redirect_blocked_reason = (
                                "Redirect blocked: file:// scheme is disabled."
                            )
                            logger.warning(redirect_blocked_reason)
                            route.abort("accessdenied")
                            return
                    elif target_scheme != "about":
                        disallowed_redirect_detected = True
                        redirect_blocked_reason = f"Redirect blocked: Forbidden scheme '{target_scheme}'."
                        logger.warning(redirect_blocked_reason)
                        route.abort("accessdenied")
                        return

            # If response is allowed, fulfill so the browser receives it
            route.fulfill(response=response)

        logger.info("Navigating to %s (timeout: %dms)...", sanitized_target, timeout)

        try:
            page.route("**/*", handle_route)
            response: Optional[Response] = page.goto(
                url,
                timeout=timeout,
                wait_until=wait_until,
            )

        except PlaywrightTimeoutError:
            err_msg = SecurityPolicy.sanitize_text(
                f"Navigation timed out after {timeout}ms while loading {sanitized_target}"
            )
            logger.error(err_msg)
            return NavigationResult(
                success=False,
                requested_url=url,
                error_message=err_msg,
            )

        except PlaywrightError as pw_err:
            if disallowed_redirect_detected:
                self._safe_reset_page(page)
                err_msg = redirect_blocked_reason or "Navigation aborted due to unauthorized redirect."
            else:
                err_msg = SecurityPolicy.sanitize_text(f"Navigation failed: {pw_err}")
            logger.error(err_msg)
            return NavigationResult(
                success=False,
                requested_url=url,
                error_message=err_msg,
            )

        finally:
            try:
                page.unroute("**/*", handle_route)
            except Exception:
                pass

        # If an unauthorised redirect was caught and aborted
        if disallowed_redirect_detected:
            self._safe_reset_page(page)
            return NavigationResult(
                success=False,
                requested_url=url,
                error_message=redirect_blocked_reason,
            )

        # 3. Post-navigation Final URL & Redirect Verification
        final_url = page.url
        sanitized_final = SecurityPolicy.sanitize_url(final_url)
        parsed_final = urlparse(final_url)

        if parsed_final.scheme not in ("file", "about"):
            if not self.security_policy.is_domain_allowed(parsed_final.hostname):
                logger.error(
                    "Security violation: Page landed on unapproved domain '%s'. Resetting page.",
                    parsed_final.hostname,
                )
                self._safe_reset_page(page)
                return NavigationResult(
                    success=False,
                    requested_url=url,
                    final_url=final_url,
                    error_message=f"Disallowed redirect: Target domain '{parsed_final.hostname}' is not in allowlist.",
                )

        status_code = response.status if response else None
        title = page.title()
        was_redirected = (final_url.rstrip("/") != url.rstrip("/"))

        logger.info(
            "Successfully navigated to %s (status: %s, title: '%s')",
            sanitized_final,
            status_code,
            title,
        )

        return NavigationResult(
            success=True,
            requested_url=url,
            final_url=final_url,
            status_code=status_code,
            title=title,
            redirected=was_redirected,
        )

    @staticmethod
    def _safe_reset_page(page: Page) -> None:
        """Safely reset a page to a blank canvas if an unapproved location was visited."""
        try:
            page.goto("about:blank")
        except Exception as e:
            logger.debug("Failed to reset page to about:blank: %s", e)
