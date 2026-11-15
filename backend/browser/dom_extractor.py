"""Extract form-control metadata from a Playwright page without reading values."""

from typing import Any, Dict, List

from playwright.sync_api import Page


class DOMExtractor:
    """Inspect supported form controls and return safe, structured metadata.

    Current input values are deliberately never read or returned.
    """

    def __init__(self, page: Page) -> None:
        self.page = page

    def extract_fields(self) -> List[Dict[str, Any]]:
        """Return metadata for input, select, and textarea controls on the page."""
        return self.page.evaluate(
            """() => {
                const controls = Array.from(
                    document.querySelectorAll("input, select, textarea")
                );
                const ignoredInputTypes = new Set([
                    "hidden", "submit", "button", "reset", "image"
                ]);

                function cleanText(value) {
                    return (value || "").replace(/\\s+/g, " ").trim();
                }

                function cssPath(element) {
                    if (element.id) {
                        const idSelector = "#" + CSS.escape(element.id);
                        if (document.querySelectorAll(idSelector).length === 1) {
                            return idSelector;
                        }
                    }

                    const parts = [];
                    let current = element;
                    while (current && current.nodeType === Node.ELEMENT_NODE) {
                        const tag = current.tagName.toLowerCase();
                        if (current.id) {
                            const idSelector = "#" + CSS.escape(current.id);
                            if (document.querySelectorAll(idSelector).length === 1) {
                                parts.unshift(idSelector);
                                break;
                            }
                        }

                        let position = 1;
                        let sibling = current.previousElementSibling;
                        while (sibling) {
                            if (sibling.tagName === current.tagName) position += 1;
                            sibling = sibling.previousElementSibling;
                        }
                        parts.unshift(`${tag}:nth-of-type(${position})`);
                        current = current.parentElement;
                    }
                    return parts.join(" > ");
                }

                return controls.flatMap((element) => {
                    const tag = element.tagName.toLowerCase();
                    const inputType = tag === "input"
                        ? (element.getAttribute("type") || "text").toLowerCase()
                        : tag;
                    if (tag === "input" && ignoredInputTypes.has(inputType)) return [];

                    let labels = Array.from(element.labels || [])
                        .map((label) => cleanText(label.textContent))
                        .filter(Boolean);
                    if (!labels.length && element.getAttribute("aria-label")) {
                        labels = [cleanText(element.getAttribute("aria-label"))];
                    }
                    if (!labels.length && element.getAttribute("aria-labelledby")) {
                        labels = element.getAttribute("aria-labelledby")
                            .split(/\\s+/)
                            .map((id) => document.getElementById(id))
                            .filter(Boolean)
                            .map((node) => cleanText(node.textContent))
                            .filter(Boolean);
                    }

                    const options = tag === "select"
                        ? Array.from(element.options).map((option) => ({
                            value: option.value,
                            label: cleanText(option.label || option.textContent),
                            disabled: option.matches(":disabled")
                        }))
                        : [];

                    return [{
                        id: element.id || null,
                        name: element.getAttribute("name"),
                        type: inputType,
                        tag: tag,
                        label: labels.length ? labels.join(" ") : null,
                        placeholder: element.getAttribute("placeholder"),
                        required: Boolean(element.required),
                        disabled: Boolean(element.disabled),
                        read_only: Boolean(element.readOnly),
                        multiple: tag === "select" && Boolean(element.multiple),
                        selector: cssPath(element),
                        options: options
                    }];
                });
            }"""
        )
