"""
ActionVani – Browser Automation Package
Member 3: Backend & Browser Automation

This package provides a secure, reusable Playwright automation foundation:
  - BrowserManager: Manages Chromium process lifecycle, context/page creation, and clean shutdown.
  - NavigationManager: Handles safe navigation, timeout recovery, and redirect enforcement.
  - SecurityPolicy: Configurable domain allowlist and URL security validation.
"""

from browser.browser_manager import BrowserManager, BrowserManagerError
from browser.navigation import NavigationManager, NavigationResult
from browser.security import (
    DEFAULT_ALLOWED_DOMAINS,
    DisallowedDomainError,
    DisallowedRedirectError,
    DisallowedSchemeError,
    SecurityError,
    SecurityPolicy,
)

__all__ = [
    "BrowserManager",
    "BrowserManagerError",
    "NavigationManager",
    "NavigationResult",
    "SecurityPolicy",
    "SecurityError",
    "DisallowedSchemeError",
    "DisallowedDomainError",
    "DisallowedRedirectError",
    "DEFAULT_ALLOWED_DOMAINS",
]

