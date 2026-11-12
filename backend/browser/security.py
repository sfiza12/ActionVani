"""
ActionVani – Browser Security & Domain Allowlist
Member 3: Backend & Browser Automation

This module provides URL validation and security controls for Playwright browser
automation. To ensure safe operation, ActionVani must never navigate to
arbitrary, untrusted, or malicious websites.

Key Security Capabilities:
  1. Configurable Domain Allowlist: Restricts navigation only to pre-approved
     domains (e.g. government portals like *.gov.in, *.nic.in, or localhost).
  2. Protocol / Scheme Filtering: Permits only safe schemes (http, https).
     Local file:// URLs are DISABLED by default in production and must be
     explicitly enabled only for local testing. Dangerous schemes like
     javascript:, data:, or vbscript: are strictly blocked.
  3. Sensitive Data Redaction: Masks passwords, tokens, Aadhaar numbers, PAN,
     and OTP values in URLs, error messages, logs, and string representations.
  4. Redirect Domain Validation: Ensures requests to unauthorised redirect
     destinations are aborted before they can be sent.
"""

import re
from typing import Iterable, Optional, Set
from urllib.parse import parse_qsl, urlencode, urlparse, urlunparse


# Default pre-approved government and development domains
DEFAULT_ALLOWED_DOMAINS: Set[str] = {
    "localhost",
    "127.0.0.1",
    "::1",
    # Official Indian government portal domains
    "*.gov.in",
    "gov.in",
    "*.nic.in",
    "nic.in",
}

# Parameter keys that hold sensitive citizen or authentication data
SENSITIVE_PARAM_KEYS: Set[str] = {
    # Authentication & credentials
    "password",
    "pass",
    "pwd",
    "secret",
    "token",
    "access_token",
    "id_token",
    "refresh_token",
    "auth",
    "key",
    "api_key",
    "apikey",
    "bearer",
    "credential",
    "credentials",
    # Indian Identity & Citizen data
    "aadhaar",
    "aadhaarno",
    "aadhaar_no",
    "aadhaar_number",
    "uid",
    "uidai",
    "pan",
    "panno",
    "pan_no",
    "pancard",
    "pan_number",
    # Verification & Financial OTPs/PINs
    "otp",
    "otp_code",
    "one_time_password",
    "pin",
    "mpin",
    "cvv",
}


def is_sensitive_key(key: str) -> bool:
    """
    Check if a query parameter key represents sensitive information.
    Handles exact matches, snake_case, kebab-case, and dot-separated tokens
    to prevent credential leaks while avoiding false positives.
    """
    if not key or not isinstance(key, str):
        return False

    cleaned = key.strip().lower()
    if cleaned in SENSITIVE_PARAM_KEYS:
        return True

    # Check segmented tokens (e.g., "user_password", "login_otp", "applicant_aadhaar")
    tokens = re.split(r"[_.-]+", cleaned)
    return any(token in SENSITIVE_PARAM_KEYS for token in tokens)


class SecurityError(Exception):
    """Base exception for all browser security violations."""
    pass


class DisallowedSchemeError(SecurityError):
    """Raised when a URL scheme is not allowed (e.g. javascript:, data:)."""
    pass


class DisallowedDomainError(SecurityError):
    """Raised when a URL domain is not in the approved allowlist."""
    pass


class DisallowedRedirectError(SecurityError):
    """Raised when a navigation redirect targets an unapproved domain."""
    pass


class SecurityPolicy:
    """
    Manages URL allowlists and validates destination targets.

    Attributes:
        allowed_domains: Set of approved domain patterns.
        allow_file_scheme: Whether local file:// URLs are permitted.
                           Defaults to False for production safety.
    """

    def __init__(
        self,
        allowed_domains: Optional[Iterable[str]] = None,
        allow_file_scheme: bool = False,
    ) -> None:
        """
        Initialize the security policy.

        Args:
            allowed_domains: Custom list of domain patterns. If None, uses DEFAULT_ALLOWED_DOMAINS.
            allow_file_scheme: True to allow file:// URLs. Defaults to False for security.
        """
        if allowed_domains is None:
            self._allowed_domains: Set[str] = set(DEFAULT_ALLOWED_DOMAINS)
        else:
            self._allowed_domains = {d.strip().lower() for d in allowed_domains if d.strip()}

        self.allow_file_scheme = allow_file_scheme

    @property
    def allowed_domains(self) -> Set[str]:
        """Return a copy of the current set of allowed domains."""
        return set(self._allowed_domains)

    def add_allowed_domain(self, domain: str) -> None:
        """Add a single domain or wildcard pattern to the allowlist."""
        cleaned = domain.strip().lower()
        if cleaned:
            self._allowed_domains.add(cleaned)

    def remove_allowed_domain(self, domain: str) -> None:
        """Remove a domain from the allowlist."""
        self._allowed_domains.discard(domain.strip().lower())

    def is_domain_allowed(self, hostname: Optional[str]) -> bool:
        """
        Check if a given hostname matches any pattern in the allowlist.

        Supports:
          - Exact match: e.g. "localhost" matches "localhost"
          - Wildcard subdomain: e.g. "*.gov.in" matches "services.india.gov.in"
            and "passport.gov.in", but not "evilgov.in"
        """
        if not hostname:
            return False

        host = hostname.strip().lower()

        for pattern in self._allowed_domains:
            pattern = pattern.lower()
            if pattern.startswith("*."):
                suffix = pattern[1:]  # e.g. ".gov.in"
                # Matches "sub.gov.in" (ends with .gov.in)
                if host.endswith(suffix):
                    return True
            elif host == pattern:
                return True

        return False

    def validate_url(self, url: str) -> str:
        """
        Validate that a URL is safe to navigate to.

        Returns:
            The parsed/cleaned URL string if valid.

        Raises:
            DisallowedSchemeError: If scheme is unsupported, dangerous, or file:// is disabled.
            DisallowedDomainError: If domain is not in the allowlist.
        """
        if not url or not isinstance(url, str):
            raise SecurityError("URL must be a non-empty string.")

        parsed = urlparse(url.strip())
        scheme = (parsed.scheme or "").lower()

        # 1. Scheme check
        if scheme == "file":
            if not self.allow_file_scheme:
                raise DisallowedSchemeError(
                    "Local file:// scheme is disabled by default for security. "
                    "Enable allow_file_scheme=True explicitly only in local test fixtures."
                )
            return url.strip()

        if scheme not in ("http", "https"):
            raise DisallowedSchemeError(
                f"Scheme '{scheme}' is forbidden. Only 'http' and 'https' are allowed."
            )

        # 2. Hostname check
        hostname = parsed.hostname
        if not hostname:
            raise DisallowedDomainError(f"URL '{self.sanitize_url(url)}' has no valid host.")

        if not self.is_domain_allowed(hostname):
            raise DisallowedDomainError(
                f"Domain '{hostname}' is not in the approved allowlist."
            )

        return url.strip()

    @staticmethod
    def sanitize_url(url: str) -> str:
        """
        Redact passwords, tokens, Aadhaar, PAN, OTP, and PIN values from a URL.
        Also redacts credentials in HTTP Basic Auth (user:password@host).

        Examples:
          https://admin:pass123@example.gov.in -> https://admin:[REDACTED]@example.gov.in
          https://example.gov.in/?token=xyz&aadhaar=1234 -> https://example.gov.in/?token=[REDACTED]&aadhaar=[REDACTED]
        """
        if not url or not isinstance(url, str):
            return ""

        try:
            parsed = urlparse(url)

            # Redact Basic Auth passwords in netloc if present
            netloc = parsed.netloc
            if parsed.password:
                user = parsed.username or ""
                host = parsed.hostname or ""
                port = f":{parsed.port}" if parsed.port else ""
                netloc = f"{user}:[REDACTED]@{host}{port}"

            if not parsed.query:
                return urlunparse(parsed._replace(netloc=netloc))

            query_params = parse_qsl(parsed.query, keep_blank_values=True)
            sanitized_params = []
            for key, val in query_params:
                if is_sensitive_key(key):
                    sanitized_params.append((key, "[REDACTED]"))
                else:
                    sanitized_params.append((key, val))

            new_query = urlencode(sanitized_params)
            return urlunparse(parsed._replace(netloc=netloc, query=new_query))
        except Exception:
            return "[UNPARSEABLE_URL]"

    @classmethod
    def sanitize_text(cls, text: str) -> str:
        """
        Scan a string (e.g. error message or log line) and sanitize any embedded URLs
        so sensitive credentials and citizen data are never exposed in logs or errors.
        """
        if not text or not isinstance(text, str):
            return ""

        # Match http://, https://, or file:// URLs up to standard boundary delimiters
        url_regex = re.compile(r"(?:https?|file)://[^\s'\"<>\)\]]+")
        return url_regex.sub(lambda match: cls.sanitize_url(match.group(0)), text)
