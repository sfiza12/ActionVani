"""
ActionVani – Browser Automation Package
Member 3: Backend & Browser Automation

This package provides a secure, reusable Playwright automation foundation:
  - BrowserManager: Manages Chromium process lifecycle, context/page creation, and clean shutdown.
  - NavigationManager: Handles safe navigation, timeout recovery, and redirect enforcement.
  - SecurityPolicy: Configurable domain allowlist and URL security validation.
  - DOMExtractor: Safe form-control metadata extraction without reading values.
  - FormFiller: Explicit field filling with per-field verification.
  - FormValidator: Required-field and native HTML validity checks.
"""

from browser.browser_manager import BrowserManager, BrowserManagerError
from browser.dom_extractor import DOMExtractor
from browser.form_filler import FormFiller
from browser.navigation import NavigationManager, NavigationResult
from browser.security import (
    DEFAULT_ALLOWED_DOMAINS,
    DisallowedDomainError,
    DisallowedRedirectError,
    DisallowedSchemeError,
    SecurityError,
    SecurityPolicy,
)
from browser.validator import FormValidator

__all__ = [
    "BrowserManager",
    "BrowserManagerError",
    "DOMExtractor",
    "FormFiller",
    "FormValidator",
    "NavigationManager",
    "NavigationResult",
    "SecurityPolicy",
    "SecurityError",
    "DisallowedSchemeError",
    "DisallowedDomainError",
    "DisallowedRedirectError",
    "DEFAULT_ALLOWED_DOMAINS",
]

