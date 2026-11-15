"""Validate required fields and browser-native HTML constraints."""

from typing import Any, Dict, List, Mapping, Optional, Sequence

from playwright.sync_api import Page

from browser.form_filler import _find_field_index


class FormValidator:
    """Check required controls, native validity, and requested-value matches."""

    def __init__(self, page: Page) -> None:
        self.page = page

    def validate(
        self,
        fields: Sequence[Mapping[str, Any]],
        requested_values: Optional[Mapping[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Return safe validation results without returning actual field values."""
        expected_by_index: Dict[int, Any] = {}
        unmatched: List[Dict[str, str]] = []
        for key, expected in (requested_values or {}).items():
            index, match_error = _find_field_index(fields, key)
            if index is None:
                unmatched.append({"field": str(key), "status": match_error or "missing_field"})
            elif index in expected_by_index and expected_by_index[index] != expected:
                unmatched.append({"field": str(key), "status": "conflicting_values"})
            else:
                field = fields[index]
                if field.get("tag") == "select":
                    expected_text = str(expected)
                    options = field.get("options", [])
                    option = next(
                        (item for item in options if str(item.get("value", "")) == expected_text),
                        None,
                    )
                    if option is None:
                        option = next(
                            (
                                item for item in options
                                if str(item.get("label", "")).casefold() == expected_text.casefold()
                            ),
                            None,
                        )
                    if option is not None:
                        expected = str(option.get("value", ""))
                expected_by_index[index] = expected

        field_results: List[Dict[str, Any]] = []
        invalid_fields: List[Dict[str, Any]] = []
        native_valid = True
        required_valid = True
        requested_inspection_failed = False

        for index, field in enumerate(fields):
            selector = field.get("selector")
            identity = {
                "id": field.get("id"),
                "name": field.get("name"),
                "label": field.get("label"),
                "selector": selector,
            }
            if not selector:
                detail = {
                    **identity,
                    "valid": False,
                    "required_missing": None,
                    "inspection_succeeded": False,
                    "inspection_status": "missing_selector",
                    "message": "The field has no usable selector.",
                    "matches_requested": None,
                }
                field_results.append(detail)
                invalid_fields.append(detail)
                native_valid = False
                if field.get("required"):
                    required_valid = False
                if index in expected_by_index:
                    requested_inspection_failed = True
                continue

            expected_present = index in expected_by_index
            expected = expected_by_index.get(index)
            try:
                state = self.page.locator(str(selector)).evaluate(
                    """(el, args) => {
                        const isCheckable = el.matches('input[type="checkbox"], input[type="radio"]');
                        const isRadio = el.matches('input[type="radio"]');
                        const isSelect = el.tagName.toLowerCase() === 'select';
                        const empty = isCheckable
                            ? !el.checked
                            : (isSelect
                                ? el.value === ''
                                : String(el.value || '').trim() === '');
                        let radioGroupMissing = false;
                        if (isRadio) {
                            const group = el.name
                                ? Array.from(document.querySelectorAll('input[type="radio"]'))
                                    .filter((radio) => radio.name === el.name && radio.form === el.form)
                                : [el];
                            radioGroupMissing = !group.some((radio) => radio.checked);
                        }
                        let matches = null;
                        if (args.hasExpected) {
                            if (el.matches('input[type="checkbox"], input[type="radio"]')) {
                                matches = el.checked === args.expected;
                            } else {
                                matches = String(el.value) === String(args.expected);
                            }
                        }
                        return {
                            valid: el.willValidate ? el.validity.valid : true,
                            message: el.willValidate ? (el.validationMessage || '') : '',
                            empty: empty,
                            radioGroupMissing: radioGroupMissing,
                            matches: matches
                        };
                    }""",
                    {"hasExpected": expected_present, "expected": expected},
                )
            except Exception:
                detail = {
                    **identity,
                    "valid": False,
                    "required_missing": None,
                    "inspection_succeeded": False,
                    "inspection_status": "failed",
                    "message": "The browser could not inspect this field.",
                    "matches_requested": None,
                }
                field_results.append(detail)
                invalid_fields.append(detail)
                native_valid = False
                if field.get("required"):
                    required_valid = False
                if index in expected_by_index:
                    requested_inspection_failed = True
                continue

            required_missing = bool(
                field.get("required")
                and not field.get("disabled")
                and not field.get("read_only")
                and (
                    state["radioGroupMissing"]
                    if field.get("type") == "radio"
                    else state["empty"]
                )
            )
            valid = bool(state["valid"])
            matches = state["matches"]
            if not valid:
                native_valid = False
            if required_missing:
                required_valid = False

            detail = {
                **identity,
                "valid": valid,
                "required_missing": required_missing,
                "inspection_succeeded": True,
                "inspection_status": "ok",
                "message": state["message"] or None,
                "matches_requested": matches,
            }
            field_results.append(detail)
            if not valid or required_missing or matches is False:
                invalid_fields.append(detail)

        values_match = not unmatched and not requested_inspection_failed and all(
            result["matches_requested"] is not False for result in field_results
        )
        return {
            "valid": not invalid_fields and not unmatched,
            "native_valid": native_valid,
            "required_valid": required_valid,
            "values_match_requested": values_match,
            "fields": field_results,
            "invalid_fields": invalid_fields,
            "unmatched_requested_fields": unmatched,
            "scope_note": (
                "This checks required fields and native HTML constraints only; "
                "it does not verify government-specific business rules."
            ),
        }
