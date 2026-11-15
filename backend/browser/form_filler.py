"""Fill supported form fields without submitting the surrounding form."""

from typing import Any, Dict, List, Mapping, Optional, Sequence, Tuple

from playwright.sync_api import Page


def _normalise_key(value: Any) -> str:
    return str(value).strip().casefold()


def _find_field_index(
    fields: Sequence[Mapping[str, Any]], key: Any
) -> Tuple[Optional[int], Optional[str]]:
    """Match by name, then ID, then label; report ambiguous matches safely."""
    wanted = _normalise_key(key)
    for attribute in ("name", "id", "label"):
        matches = [
            index
            for index, field in enumerate(fields)
            if field.get(attribute) is not None
            and _normalise_key(field.get(attribute)) == wanted
        ]
        if len(matches) == 1:
            return matches[0], None
        if len(matches) > 1:
            return None, "ambiguous_field"
    return None, "missing_field"


class FormFiller:
    """Fill fields described by ``DOMExtractor`` and return value-free results."""

    def __init__(self, page: Page) -> None:
        self.page = page

    def fill_fields(
        self,
        fields: Sequence[Mapping[str, Any]],
        values: Mapping[str, Any],
    ) -> Dict[str, Any]:
        """Fill requested controls and verify each value without clicking submit.

        ``values`` is keyed by a field's name, ID, or associated label. Result
        records deliberately exclude requested and actual field values.
        """
        results: List[Dict[str, Any]] = []
        assigned: Dict[int, Tuple[str, Any]] = {}

        for key, value in values.items():
            index, match_error = _find_field_index(fields, key)
            if match_error:
                results.append({
                    "field": str(key),
                    "status": match_error,
                    "verified": False,
                    "message": (
                        "More than one field matches this key."
                        if match_error == "ambiguous_field"
                        else "No field matches this key."
                    ),
                })
                continue

            assert index is not None
            if index in assigned:
                previous_key, previous_value = assigned[index]
                if previous_value != value:
                    results.append({
                        "field": str(key),
                        "status": "conflicting_values",
                        "verified": False,
                        "message": f"This field already has a different value requested via '{previous_key}'.",
                    })
                continue
            assigned[index] = (str(key), value)

        for index, (key, value) in assigned.items():
            field = fields[index]
            selector = field.get("selector")
            base = {"field": key, "selector": selector}

            if not selector:
                results.append({**base, "status": "missing_selector", "verified": False,
                                "message": "The field has no usable selector."})
                continue
            if field.get("disabled"):
                results.append({**base, "status": "disabled", "verified": False,
                                "message": "Disabled fields cannot be filled."})
                continue
            if field.get("read_only"):
                results.append({**base, "status": "read_only", "verified": False,
                                "message": "Read-only fields cannot be filled."})
                continue

            field_type = str(field.get("type", "")).lower()
            tag = str(field.get("tag", "")).lower()
            locator = self.page.locator(str(selector))

            try:
                if field_type == "checkbox":
                    if not isinstance(value, bool):
                        results.append({**base, "status": "invalid_value", "verified": False,
                                        "message": "Checkbox values must be true or false."})
                        continue
                    if value:
                        locator.check()
                    else:
                        locator.uncheck()
                    verified = locator.is_checked() is value
                elif field_type in {"text", "date"} or tag == "textarea":
                    text_value = str(value)
                    locator.fill(text_value)
                    verified = locator.input_value() == text_value
                elif tag == "select" or field_type == "select":
                    if field.get("multiple"):
                        results.append({**base, "status": "unsupported_multiple_select", "verified": False,
                                        "message": "Multi-select dropdowns are not supported."})
                        continue
                    option = self._find_option(field, value)
                    if option is None:
                        results.append({**base, "status": "unsupported_option", "verified": False,
                                        "message": "No dropdown option matches the requested value."})
                        continue
                    if option.get("disabled"):
                        results.append({**base, "status": "disabled_option", "verified": False,
                                        "message": "The requested dropdown option is disabled."})
                        continue
                    locator.select_option(value=str(option.get("value", "")))
                    verified = locator.input_value() == str(option.get("value", ""))
                else:
                    results.append({**base, "status": "unsupported", "verified": False,
                                    "message": "This field type is not supported for automatic filling."})
                    continue
            except Exception:
                # Do not surface browser exception text, which could contain field data.
                results.append({**base, "status": "fill_failed", "verified": False,
                                "message": "The browser could not fill this field."})
                continue

            results.append({
                **base,
                "status": "filled" if verified else "verification_failed",
                "verified": verified,
                "message": None if verified else "The browser value did not match the requested value.",
            })

        successful = all(result.get("status") == "filled" for result in results)
        return {"success": successful, "results": results}

    @staticmethod
    def _find_option(field: Mapping[str, Any], requested: Any) -> Optional[Mapping[str, Any]]:
        wanted = str(requested)
        options = field.get("options", [])
        for option in options:
            if str(option.get("value", "")) == wanted:
                return option
        for option in options:
            if str(option.get("label", "")).casefold() == wanted.casefold():
                return option
        return None
