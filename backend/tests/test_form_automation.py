"""Offline Playwright tests for safe form extraction, filling, and validation."""

from pathlib import Path

import pytest

from browser import (
    BrowserManager,
    DOMExtractor,
    FormFiller,
    FormValidator,
    NavigationManager,
    SecurityPolicy,
)


FIXTURE_FORM_PATH = Path(__file__).resolve().parents[1] / "test_form.html"


@pytest.fixture
def page():
    """Open the local fixture through the existing security-aware navigator."""
    with BrowserManager(headless=True) as browser_manager:
        browser_page = browser_manager.new_page()
        navigation = NavigationManager(
            security_policy=SecurityPolicy(allow_file_scheme=True)
        )
        result = navigation.navigate(browser_page, FIXTURE_FORM_PATH.as_uri())
        assert result.success, result.error_message
        yield browser_page


def test_dom_extraction_labels_required_fields_and_dropdown_options(page):
    fields = DOMExtractor(page).extract_fields()
    by_name = {field["name"]: field for field in fields if field["name"]}

    assert {"name", "dob", "gender", "agreement"}.issubset(by_name)
    assert by_name["name"]["label"] == "Full Name:"
    assert by_name["name"]["required"] is True
    assert by_name["dob"]["label"] == "Date of Birth:"
    assert by_name["dob"]["required"] is True
    assert by_name["nickname"]["label"] is None

    gender_options = by_name["gender"]["options"]
    assert [(option["value"], option["label"]) for option in gender_options] == [
        ("", "Select Gender"),
        ("male", "Male"),
        ("female", "Female"),
        ("other", "Other"),
    ]

    # Extracted records contain no live value, even for the read-only fixture field.
    assert all("value" not in field for field in fields)
    assert all(page.locator(field["selector"]).count() == 1 for field in fields)


def test_text_date_and_dropdown_values_are_filled_and_verified(page):
    fields = DOMExtractor(page).extract_fields()
    result = FormFiller(page).fill_fields(
        fields,
        {"name": "Asha Rao", "dob": "2002-04-23", "gender": "female"},
    )

    assert result["success"] is True
    assert all(item["verified"] for item in result["results"])
    assert page.locator("#name").input_value() == "Asha Rao"
    assert page.locator("#dob").input_value() == "2002-04-23"
    assert page.locator("#gender").input_value() == "female"


def test_dropdown_can_be_selected_by_visible_label(page):
    fields = DOMExtractor(page).extract_fields()
    result = FormFiller(page).fill_fields(fields, {"Gender:": "Other"})

    assert result["success"] is True
    assert page.locator("#gender").input_value() == "other"
    validation = FormValidator(page).validate(fields, {"Gender:": "Other"})
    assert validation["values_match_requested"] is True


def test_checkbox_can_be_checked_and_unchecked(page):
    fields = DOMExtractor(page).extract_fields()
    filler = FormFiller(page)

    checked = filler.fill_fields(fields, {"agreement": True})
    assert checked["success"] is True
    assert page.locator("#agreement").is_checked()

    unchecked = filler.fill_fields(fields, {"agreement": False})
    assert unchecked["success"] is True
    assert not page.locator("#agreement").is_checked()


def test_missing_disabled_read_only_and_unsupported_fields_are_reported(page):
    fields = DOMExtractor(page).extract_fields()
    result = FormFiller(page).fill_fields(
        fields,
        {
            "does-not-exist": "ignored",
            "disabledField": "cannot fill",
            "readOnlyField": "cannot fill",
            "attachment": "unsupported",
        },
    )

    statuses = {item["field"]: item["status"] for item in result["results"]}
    assert result["success"] is False
    assert statuses == {
        "does-not-exist": "missing_field",
        "disabledField": "disabled",
        "readOnlyField": "read_only",
        "attachment": "unsupported",
    }
    assert page.locator("#disabledField").input_value() == ""
    assert page.locator("#readOnlyField").input_value() == "locked"


def test_required_validation_handles_radio_groups(page):
    page.evaluate(
        """() => {
            const form = document.querySelector('#registrationForm');
            form.insertAdjacentHTML('beforeend',
                '<label><input id="radioHome" type="radio" name="delivery" value="home" required>Home</label>' +
                '<label><input id="radioPickup" type="radio" name="delivery" value="pickup">Pickup</label>');
            document.querySelector('#radioPickup').checked = true;
        }"""
    )
    fields = DOMExtractor(page).extract_fields()
    FormFiller(page).fill_fields(fields, {"name": "Asha Rao", "dob": "2002-04-23"})

    result = FormValidator(page).validate(fields)
    radio_result = next(item for item in result["fields"] if item["id"] == "radioHome")
    assert radio_result["required_missing"] is False
    assert result["required_valid"] is True


def test_validator_marks_required_field_with_missing_selector_uninspected(page):
    fields = DOMExtractor(page).extract_fields()
    name_field = next(field for field in fields if field["name"] == "name")
    name_field["selector"] = None

    result = FormValidator(page).validate(fields, {"name": "Private Citizen Value"})
    name_result = next(item for item in result["fields"] if item["name"] == "name")

    assert result["values_match_requested"] is False
    assert result["required_valid"] is False
    assert name_result["inspection_succeeded"] is False
    assert name_result["inspection_status"] == "missing_selector"
    assert name_result["required_missing"] is None
    assert "Private Citizen Value" not in str(result)


def test_validator_marks_playwright_inspection_failure_uninspected(page):
    fields = DOMExtractor(page).extract_fields()
    name_field = next(field for field in fields if field["name"] == "name")
    name_field["selector"] = "??invalid-selector??"

    result = FormValidator(page).validate(fields, {"name": "Private Citizen Value"})
    name_result = next(item for item in result["fields"] if item["name"] == "name")

    assert result["values_match_requested"] is False
    assert result["required_valid"] is False
    assert name_result["inspection_succeeded"] is False
    assert name_result["inspection_status"] == "failed"
    assert name_result["required_missing"] is None
    assert "Private Citizen Value" not in str(result)


def test_multi_select_dropdown_is_reported_as_unsupported(page):
    page.evaluate(
        """() => {
            const select = document.createElement('select');
            select.id = 'topics';
            select.name = 'topics';
            select.multiple = true;
            select.add(new Option('Health', 'health'));
            document.querySelector('#registrationForm').append(select);
        }"""
    )
    fields = DOMExtractor(page).extract_fields()
    topics_field = next(field for field in fields if field["name"] == "topics")
    result = FormFiller(page).fill_fields(fields, {"topics": "health"})

    assert topics_field["multiple"] is True
    assert result["success"] is False
    assert result["results"][0]["status"] == "unsupported_multiple_select"


def test_disabled_dropdown_option_is_reported_clearly(page):
    page.evaluate(
        """() => {
            const option = new Option('Unavailable', 'unavailable');
            option.disabled = true;
            document.querySelector('#gender').add(option);
        }"""
    )
    fields = DOMExtractor(page).extract_fields()
    result = FormFiller(page).fill_fields(fields, {"gender": "unavailable"})

    assert result["success"] is False
    assert result["results"][0]["status"] == "disabled_option"
    assert "unavailable" not in str(result)


def test_ambiguous_field_matching_is_reported_without_values(page):
    page.evaluate(
        """() => {
            const duplicate = document.createElement('input');
            duplicate.type = 'text';
            duplicate.id = 'secondName';
            duplicate.name = 'name';
            document.querySelector('#registrationForm').append(duplicate);
        }"""
    )
    fields = DOMExtractor(page).extract_fields()
    result = FormFiller(page).fill_fields(fields, {"name": "Private Citizen Value"})

    assert result["success"] is False
    assert result["results"][0]["status"] == "ambiguous_field"
    assert "Private Citizen Value" not in str(result)


def test_conflicting_requested_values_are_reported_without_values(page):
    page.evaluate(
        """() => {
            const input = document.createElement('input');
            input.type = 'text';
            input.id = 'fullNameAlias';
            input.name = 'fullName';
            document.querySelector('#registrationForm').append(input);
        }"""
    )
    fields = DOMExtractor(page).extract_fields()
    result = FormFiller(page).fill_fields(
        fields,
        {"fullName": "Private Value One", "fullNameAlias": "Private Value Two"},
    )

    assert result["success"] is False
    assert any(item["status"] == "conflicting_values" for item in result["results"])
    assert "Private Value One" not in str(result)
    assert "Private Value Two" not in str(result)


def test_required_fields_are_reported_when_empty(page):
    fields = DOMExtractor(page).extract_fields()
    result = FormValidator(page).validate(fields)

    assert result["valid"] is False
    assert result["native_valid"] is False
    assert result["required_valid"] is False
    missing = {item["name"] for item in result["invalid_fields"] if item["required_missing"]}
    assert missing == {"name", "dob"}
    assert all(item["message"] for item in result["invalid_fields"])


def test_valid_form_and_requested_value_mismatch(page):
    fields = DOMExtractor(page).extract_fields()
    FormFiller(page).fill_fields(
        fields,
        {"name": "Asha Rao", "dob": "2002-04-23", "gender": "female"},
    )

    valid = FormValidator(page).validate(
        fields,
        {"name": "Asha Rao", "dob": "2002-04-23", "gender": "female"},
    )
    assert valid["valid"] is True
    assert valid["native_valid"] is True
    assert valid["required_valid"] is True
    assert valid["values_match_requested"] is True

    mismatch = FormValidator(page).validate(fields, {"name": "Different Name"})
    assert mismatch["valid"] is False
    assert mismatch["values_match_requested"] is False
    assert any(item["name"] == "name" for item in mismatch["invalid_fields"])
    assert "Asha Rao" not in str(mismatch)


def test_automation_never_submits_the_form(page):
    fields = DOMExtractor(page).extract_fields()
    page.evaluate(
        """() => {
            window.__submitCount = 0;
            document.querySelector('#registrationForm').addEventListener('submit', () => {
                window.__submitCount += 1;
            });
        }"""
    )

    FormFiller(page).fill_fields(fields, {"name": "Asha Rao", "dob": "2002-04-23"})
    FormValidator(page).validate(fields)

    assert page.evaluate("window.__submitCount") == 0
    assert page.locator("#result").inner_text() == ""
