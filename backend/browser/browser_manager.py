"""
ActionVani – Browser Manager
Member 3: Backend & Browser Automation

This module manages the lifecycle of Chromium browser instances using Playwright.

Responsibilities:
  - Launching Chromium safely in headless (production/test) or headed (visual debugging) modes.
  - Creating browser contexts and pages with consistent timeouts and settings.
  - Ensuring clean resource disposal (no orphaned Chromium or Node processes).
  - Providing Python context manager support (`with BrowserManager() as bm:`).
"""

import logging
from typing import List, Optional
from playwright.sync_api import (
    Browser,
    BrowserContext,
    Error as PlaywrightError,
    Page,
    Playwright,
    sync_playwright,
)

logger = logging.getLogger("actionvani.browser")


class BrowserManagerError(Exception):
    """Raised when an error occurs during browser lifecycle management."""
    pass


class BrowserManager:
    """
    Manages Playwright and Chromium browser instances.

    Example usage (context manager - recommended):
        ```python
        with BrowserManager(headless=True) as bm:
            page = bm.new_page()
            page.goto("https://services.india.gov.in")
            # Resources are automatically closed when exiting the block
        ```

    Example usage (manual lifecycle):
        ```python
        bm = BrowserManager(headless=True)
        bm.start()
        try:
            page = bm.new_page()
            ...
        finally:
            bm.close()
        ```
    """

    def __init__(
        self,
        headless: bool = True,
        slow_mo: int = 0,
        default_timeout_ms: int = 30000,
    ) -> None:
        """
        Initialize the browser manager configuration.

        Args:
            headless: Whether to run Chromium in the background without UI (True)
                      or with a visible window (False).
            slow_mo: Milliseconds to wait between actions (useful for visual debugging).
            default_timeout_ms: Default timeout for page operations in milliseconds.
        """
        self.headless: bool = headless
        self.slow_mo: int = slow_mo
        self.default_timeout_ms: int = default_timeout_ms

        self._playwright: Optional[Playwright] = None
        self._browser: Optional[Browser] = None
        self._contexts: List[BrowserContext] = []
        self._pages: List[Page] = []
        self._is_running: bool = False

    @property
    def is_running(self) -> bool:
        """Return True if the browser instance is currently active and open."""
        return self._is_running and self._browser is not None and self._browser.is_connected()

    def start(self) -> "BrowserManager":
        """
        Launch the Playwright driver and the Chromium browser.

        Returns:
            The BrowserManager instance (self) for chaining.
        """
        if self.is_running:
            logger.debug("Browser is already running.")
            return self

        try:
            logger.info("Starting Playwright driver...")
            self._playwright = sync_playwright().start()

            logger.info(
                "Launching Chromium (headless=%s, slow_mo=%dms)...",
                self.headless,
                self.slow_mo,
            )
            self._browser = self._playwright.chromium.launch(
                headless=self.headless,
                slow_mo=self.slow_mo,
                args=[
                    "--no-sandbox",
                    "--disable-setuid-sandbox",
                    "--disable-dev-shm-usage",
                ],
            )
            self._is_running = True
            logger.info("Chromium launched successfully.")
            return self

        except Exception as exc:
            logger.error("Failed to start browser: %s", exc)
            self.close()  # Clean up any partial resources
            raise BrowserManagerError(f"Could not launch browser: {exc}") from exc

    def new_context(self, **kwargs) -> BrowserContext:
        """
        Create a new isolated browser context (like an incognito session).

        Args:
            **kwargs: Extra arguments forwarded to Playwright's browser.new_context().

        Returns:
            A new BrowserContext instance.
        """
        if not self.is_running or self._browser is None:
            self.start()

        assert self._browser is not None
        context = self._browser.new_context(**kwargs)
        context.set_default_timeout(self.default_timeout_ms)
        self._contexts.append(context)
        return context

    def new_page(self, context: Optional[BrowserContext] = None) -> Page:
        """
        Create a new browser tab/page.

        Args:
            context: Optional browser context to create the page in. If omitted,
                     creates a page in a default managed context.

        Returns:
            A new Page instance.
        """
        if not self.is_running:
            self.start()

        if context is not None:
            page = context.new_page()
        else:
            ctx = self.new_context()
            page = ctx.new_page()

        page.set_default_timeout(self.default_timeout_ms)
        self._pages.append(page)
        return page

    def close(self) -> None:
        """
        Safely shut down all pages, contexts, browser processes, and driver resources.
        Guaranteed not to raise an uncaught exception, so it is safe to call in
        error recovery handlers or `finally` blocks.
        """
        logger.info("Closing browser resources...")

        # 1. Close all opened pages
        for page in list(self._pages):
            try:
                if not page.is_closed():
                    page.close()
            except Exception as e:
                logger.debug("Error closing page: %s", e)
        self._pages.clear()

        # 2. Close all opened contexts
        for context in list(self._contexts):
            try:
                context.close()
            except Exception as e:
                logger.debug("Error closing context: %s", e)
        self._contexts.clear()

        # 3. Close the browser instance
        if self._browser is not None:
            try:
                self._browser.close()
            except Exception as e:
                logger.debug("Error closing browser: %s", e)
            finally:
                self._browser = None

        # 4. Stop the Playwright driver process
        if self._playwright is not None:
            try:
                self._playwright.stop()
            except Exception as e:
                logger.debug("Error stopping Playwright: %s", e)
            finally:
                self._playwright = None

        self._is_running = False
        logger.info("Browser resources cleanly closed.")

    def __enter__(self) -> "BrowserManager":
        """Enter context manager block."""
        return self.start()

    def __exit__(self, exc_type, exc_val, exc_tb) -> None:
        """Exit context manager block, safely closing all resources."""
        self.close()

