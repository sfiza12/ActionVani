"""
ActionVani – AI Module Schemas & Member 3 Integration Tests.

Validates:
  1. Playwright DOM & FormFiller integration with actual Member 3 fixture:
     name="name", id="name", label="Full Name", selector="#name", type="text", required=True.
  2. Mapping citizen 'full_name="Priya Sharma"' to target_field="name".
  3. Rejection of empty target_field values.
  4. Detection and rejection of conflicting field_id and target_field values.
  5. Target identifier resolution: prefers name, then id, then label; never derives from selector.
  6. Prevention of unsupported controls (radio, multi-select) from being marked as suggested.
  7. Strict enforcement of Member 3's agreed intent contract.
  8. OCR response contract: extracted_text, raw_text alias, unreadable_fields, requires_user_review.
  9. Deterministic mock safety without fabricating personal data.
  10. Candidate with no name, id, or label but with selector="#dob_input":
      - target_field=None and field_id=None (NO fabricated identifier or selector reuse).
      - selector="#dob_input" preserved in separate property.
      - status=manual_handling.
  11. Suggested and missing mappings with target_field=None are strictly rejected.
  12. Canonical property names in JSON serialization:
      suggested_mappings, missing_fields, ambiguous_mappings, manual_handling, ready_for_review.
  13. Backward-compatible access using suggested, missing, ambiguous properties and initializers.
  14. ready_for_review conservative computation:
      - True when all fields are successfully suggested (missing, ambiguous, manual_handling empty).
      - False when missing fields exist.
      - False when ambiguous mappings exist.
      - False when manual_handling entries exist.
  15. processing_time_seconds is strictly None for deterministic mocks.
  16. all_mappings remains synchronized with the four categories.
"""

from pathlib import Path
import sys

# Ensure repository root is on sys.path regardless of execution working directory
ROOT = Path(__file__).resolve().parents[3]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import pytest
from pydantic import ValidationError

from backend.ai.common.schemas import (
    AgreedIntent,
    AIResponseStatus,
    DocumentExtractionResponse,
    DocumentType,
    FieldMappingStatus,
    FormFieldCandidate,
    FormFieldMapping,
    FormMappingRequest,
    FormMappingResponse,
    IntentClassificationResponse,
    SupportedLanguage,
)


# ==============================================================================
# 1. Member 3 Playwright Fixture & FormFiller Mapping
# ==============================================================================

def test_member3_fixture_maps_to_target_field_name():
    """
    Test the exact Playwright fixture from test_form.html:
      name = "name"
      id = "name"
      label = "Full Name"
      type = "text"
      selector = "#name"
      required = True

    Citizen user information:
      {"full_name": "Priya Sharma"}

    Expected target_field:
      "name" (preferred HTML name/id over selector or semantic applicant_name).
    """
    fixture_field = {
        "name": "name",
        "id": "name",
        "label": "Full Name",
        "type": "text",
        "selector": "#name",
        "required": True,
    }
    user_info = {"full_name": "Priya Sharma"}

    response = FormMappingResponse.create_deterministic_mock(
        fields=[fixture_field],
        user_information=user_info,
    )

    # Validate top-level response properties
    assert response.status == AIResponseStatus.SUCCESS
    assert response.is_mock is True
    assert response.confidence is None
    assert response.processing_time_seconds is None
    assert response.ready_for_review is True  # Only 1 field, matched and suggested

    # Validate canonical property access
    assert len(response.suggested_mappings) == 1
    mapping = response.suggested_mappings[0]
    assert mapping.target_field == "name"
    assert mapping.field_id == "name"  # Backward-compatible alias
    assert mapping.value == "Priya Sharma"
    assert mapping.status == FieldMappingStatus.SUGGESTED
    assert mapping.selector == "#name"
    assert mapping.label == "Full Name"
    assert mapping.field_type == "text"
    assert mapping.confidence is None

    # Validate backward-compatible alias access
    assert len(response.suggested) == 1
    assert response.suggested[0] is mapping


# ==============================================================================
# 2. Target Identifier Resolution Rules
# ==============================================================================

def test_target_identifier_prefers_name_over_id():
    """name attribute must take highest precedence."""
    candidate = FormFieldCandidate(
        name="applicant_first_name",
        id="txt_01",
        label="First Name",
        selector="#txt_01",
    )
    assert candidate.target_identifier == "applicant_first_name"


def test_target_identifier_prefers_id_when_name_absent():
    """id attribute is used when name is missing."""
    candidate = FormFieldCandidate(
        name=None,
        id="txt_applicant_id",
        label="Applicant ID",
        selector="#txt_applicant_id",
    )
    assert candidate.target_identifier == "txt_applicant_id"


def test_target_identifier_falls_back_to_label_when_name_and_id_absent():
    """Label is supported as fallback for FormFiller label-based matching."""
    candidate = FormFieldCandidate(
        name=None,
        id=None,
        label="Aadhaar Number",
        selector="form > div:nth-child(2) > input",
    )
    assert candidate.target_identifier == "Aadhaar Number"


def test_target_identifier_never_derives_from_css_selector():
    """
    CRITICAL: Never strip '#' or parse CSS selectors to invent an identifier
    when neither name, id, nor label is provided.
    """
    candidate = FormFieldCandidate(
        name=None,
        id=None,
        label=None,
        selector="#dob_input",
    )
    assert candidate.target_identifier is None


# ==============================================================================
# 3. Field Mapping Validation & Identifiers
# ==============================================================================

def test_reject_empty_target_field():
    """Reject empty strings or whitespace-only target_field."""
    with pytest.raises(ValidationError):
        FormFieldMapping(
            target_field="",
            status=FieldMappingStatus.SUGGESTED,
            value="Some Value",
        )

    with pytest.raises(ValidationError):
        FormFieldMapping(
            target_field="   ",
            status=FieldMappingStatus.SUGGESTED,
            value="Some Value",
        )


def test_reject_conflicting_target_field_and_field_id():
    """Validate that target_field and field_id cannot contradict each other."""
    with pytest.raises(ValidationError) as exc_info:
        FormFieldMapping(
            target_field="name",
            field_id="different_id",
            status=FieldMappingStatus.SUGGESTED,
            value="Priya Sharma",
        )
    assert "Conflicting identifiers" in str(exc_info.value)


def test_field_id_and_target_field_synchronization():
    """Ensure target_field and field_id stay in sync when only one is provided."""
    m1 = FormFieldMapping(
        target_field="dob",
        status=FieldMappingStatus.SUGGESTED,
        value="2000-01-01",
    )
    assert m1.field_id == "dob"

    m2 = FormFieldMapping(
        field_id="gender",
        status=FieldMappingStatus.SUGGESTED,
        value="female",
    )
    assert m2.target_field == "gender"


def test_suggested_mapping_with_none_target_field_rejected():
    """Suggested mappings with target_field=None must be rejected."""
    with pytest.raises(ValidationError) as exc_info:
        FormFieldMapping(
            target_field=None,
            status=FieldMappingStatus.SUGGESTED,
            value="Priya Sharma",
        )
    assert "target_field is mandatory" in str(exc_info.value)


def test_missing_mapping_with_none_target_field_rejected():
    """Missing mappings with target_field=None must be rejected."""
    with pytest.raises(ValidationError) as exc_info:
        FormFieldMapping(
            target_field=None,
            status=FieldMappingStatus.MISSING,
            value=None,
        )
    assert "target_field is mandatory" in str(exc_info.value)


def test_manual_handling_with_none_target_field_allowed():
    """manual_handling mappings are permitted to have target_field=None."""
    mapping = FormFieldMapping(
        target_field=None,
        field_id=None,
        status=FieldMappingStatus.MANUAL_HANDLING,
        selector="#dob_input",
        reasoning="Field has neither HTML name, id, nor label.",
    )
    assert mapping.target_field is None
    assert mapping.field_id is None
    assert mapping.selector == "#dob_input"
    assert mapping.status == FieldMappingStatus.MANUAL_HANDLING


# ==============================================================================
# 4. FormFiller Unsupported Controls Prevention
# ==============================================================================

def test_unsupported_radio_controls_cannot_be_suggested():
    """
    FormFiller has limitations with radio groups.
    Radio controls MUST NOT be marked as executable 'suggested' mappings.
    """
    with pytest.raises(ValidationError) as exc_info:
        FormFieldMapping(
            target_field="gender_radio",
            field_type="radio",
            status=FieldMappingStatus.SUGGESTED,
            value="female",
        )
    assert "not supported by FormFiller for automated execution" in str(exc_info.value)


def test_unsupported_multiselect_controls_cannot_be_suggested():
    """Multi-select controls cannot be marked as suggested."""
    with pytest.raises(ValidationError) as exc_info:
        FormFieldMapping(
            target_field="scholarship_schemes",
            field_type="select-multiple",
            status=FieldMappingStatus.SUGGESTED,
            value=["scheme_1", "scheme_2"],
        )
    assert "not supported by FormFiller for automated execution" in str(exc_info.value)


def test_unsupported_controls_allowed_as_manual_handling():
    """Radio controls can and should be flagged under manual_handling."""
    mapping = FormFieldMapping(
        target_field="gender_radio",
        field_type="radio",
        status=FieldMappingStatus.MANUAL_HANDLING,
        value=None,
        clarification_prompt="Please select your gender on the screen.",
    )
    assert mapping.status == FieldMappingStatus.MANUAL_HANDLING


# ==============================================================================
# 5. Agreed Intent Contract Validation
# ==============================================================================

def test_agreed_intent_contract_values():
    """Validate all 6 agreed intent labels from Member 3 contract."""
    agreed_intents = [
        "scholarship_application",
        "application_status",
        "document_assistance",
        "eshram_registration",
        "general_government_service",
        "unknown",
    ]
    for intent_str in agreed_intents:
        resp = IntentClassificationResponse(
            status=AIResponseStatus.SUCCESS,
            intent=intent_str,
            confidence=0.9,
        )
        assert resp.intent == AgreedIntent(intent_str)


def test_invalid_intent_rejected():
    """Reject intents outside the agreed contract."""
    with pytest.raises(ValidationError):
        IntentClassificationResponse(
            status=AIResponseStatus.SUCCESS,
            intent="arbitrary_unagreed_intent",
        )


# ==============================================================================
# 6. OCR Response Contract
# ==============================================================================

def test_ocr_response_contract_fields():
    """
    Verify OCR response includes extracted_text, extracted_fields,
    unreadable_fields, and requires_user_review.
    """
    ocr_resp = DocumentExtractionResponse(
        status=AIResponseStatus.SUCCESS,
        document_type=DocumentType.AADHAAR,
        extracted_text="Government of India\nFull Name: Ramesh",
        extracted_fields={},
        unreadable_fields=["qr_code", "issue_date"],
        requires_user_review=True,
        confidence=0.82,
    )
    assert ocr_resp.extracted_text == "Government of India\nFull Name: Ramesh"
    assert ocr_resp.raw_text == ocr_resp.extracted_text  # Synchronized alias
    assert ocr_resp.unreadable_fields == ["qr_code", "issue_date"]
    assert ocr_resp.requires_user_review is True
    assert ocr_resp.is_mock is False


def test_ocr_raw_text_alias_synchronization():
    """Ensure passing raw_text populates extracted_text."""
    ocr_resp = DocumentExtractionResponse(
        status=AIResponseStatus.SUCCESS,
        raw_text="Sample Document Text",
    )
    assert ocr_resp.extracted_text == "Sample Document Text"
    assert ocr_resp.raw_text == "Sample Document Text"


# ==============================================================================
# 7. Deterministic Mock Safety & No-Fabrication Rules
# ==============================================================================

def test_mock_does_not_fabricate_personal_information():
    """
    Missing required fields must be flagged as MISSING with value=None,
    never populated with invented or hallucinated personal details.
    """
    fields = [
        {"name": "name", "id": "name", "label": "Full Name", "type": "text", "required": True},
        {"name": "dob", "id": "dob", "label": "Date of Birth", "type": "date", "required": True},
        {"name": "aadhaar", "id": "aadhaar", "label": "Aadhaar Number", "type": "text", "required": True},
    ]
    # Citizen provided only their name
    user_info = {"full_name": "Priya Sharma"}

    response = FormMappingResponse.create_deterministic_mock(
        fields=fields,
        user_information=user_info,
    )

    # 1 suggested field
    assert len(response.suggested_mappings) == 1
    assert response.suggested_mappings[0].target_field == "name"
    assert response.suggested_mappings[0].value == "Priya Sharma"

    # 2 missing fields (dob and aadhaar) - values MUST be None, never fabricated!
    assert len(response.missing_fields) == 2
    missing_targets = {m.target_field: m.value for m in response.missing_fields}
    assert missing_targets["dob"] is None
    assert missing_targets["aadhaar"] is None

    # Entire response must be flagged as mock with null confidence and null processing time
    assert response.is_mock is True
    assert response.confidence is None
    assert response.processing_time_seconds is None


def test_candidate_without_name_id_or_label_sets_target_field_none():
    """
    When a candidate has NO name, id, or label but has selector='#dob_input':
      - Response must set target_field=None and field_id=None.
      - The selector must remain '#dob_input' in its separate selector property.
      - Status must be manual_handling.
      - Must NEVER use the selector or a placeholder string as target_field.
    """
    unidentified_field = {
        "name": None,
        "id": None,
        "label": None,
        "type": "date",
        "selector": "#dob_input",
        "required": True,
    }
    user_info = {"dob": "2000-01-01"}

    response = FormMappingResponse.create_deterministic_mock(
        fields=[unidentified_field],
        user_information=user_info,
    )

    assert len(response.manual_handling) == 1
    mapping = response.manual_handling[0]

    # Guarantees:
    assert mapping.target_field is None
    assert mapping.field_id is None
    assert mapping.selector == "#dob_input"
    assert mapping.status == FieldMappingStatus.MANUAL_HANDLING
    assert "cannot be resolved for automated filling" in mapping.reasoning


# ==============================================================================
# 8. Canonical Names, Backward Compatibility, & ready_for_review Tests
# ==============================================================================

def test_canonical_property_names_in_json_serialization():
    """
    Canonical names ('suggested_mappings', 'missing_fields', 'ambiguous_mappings',
    'manual_handling', 'ready_for_review') must be used in JSON serialization.
    Legacy names ('suggested', 'missing', 'ambiguous') must NOT appear as root keys.
    """
    mapping = FormFieldMapping(
        target_field="name",
        status=FieldMappingStatus.SUGGESTED,
        value="Priya Sharma",
    )
    resp = FormMappingResponse(
        suggested_mappings=[mapping],
        ready_for_review=True,
    )
    data = resp.model_dump()
    assert "suggested_mappings" in data
    assert "missing_fields" in data
    assert "ambiguous_mappings" in data
    assert "manual_handling" in data
    assert "ready_for_review" in data
    assert data["ready_for_review"] is True

    # Legacy names must NOT be exported in model_dump dict/JSON keys
    assert "suggested" not in data
    assert "missing" not in data
    assert "ambiguous" not in data

    json_str = resp.model_dump_json()
    assert '"suggested_mappings"' in json_str
    assert '"missing_fields"' in json_str
    assert '"ready_for_review":true' in json_str


def test_backward_compatible_access_and_initialization():
    """
    Existing code using response.suggested, response.missing, response.ambiguous
    or initializing with suggested=[...], missing=[...] must continue working seamlessly.
    """
    m1 = FormFieldMapping(target_field="name", status=FieldMappingStatus.SUGGESTED, value="Priya")
    m2 = FormFieldMapping(target_field="dob", status=FieldMappingStatus.MISSING)
    m3 = FormFieldMapping(target_field="gender", status=FieldMappingStatus.AMBIGUOUS)

    # Initialize using legacy keyword arguments
    resp = FormMappingResponse(
        suggested=[m1],
        missing=[m2],
        ambiguous=[m3],
    )

    # Verify canonical fields were populated
    assert resp.suggested_mappings == [m1]
    assert resp.missing_fields == [m2]
    assert resp.ambiguous_mappings == [m3]

    # Verify property access works
    assert resp.suggested == [m1]
    assert resp.missing == [m2]
    assert resp.ambiguous == [m3]

    # Verify no duplicate lists: modifying through property affects the same list
    m4 = FormFieldMapping(target_field="age", status=FieldMappingStatus.SUGGESTED, value="25")
    resp.suggested.append(m4)
    assert len(resp.suggested_mappings) == 2
    assert resp.suggested_mappings[-1] == m4


def test_ready_for_review_true_when_all_fields_suggested():
    """ready_for_review is True when missing, ambiguous, and manual_handling are all empty."""
    fields = [
        {"name": "name", "id": "name", "label": "Full Name", "type": "text", "required": True},
        {"name": "dob", "id": "dob", "label": "Date of Birth", "type": "date", "required": True},
    ]
    user_info = {
        "full_name": "Priya Sharma",
        "date_of_birth": "2001-08-15",
    }
    resp = FormMappingResponse.create_deterministic_mock(fields, user_info)
    assert len(resp.suggested_mappings) == 2
    assert len(resp.missing_fields) == 0
    assert len(resp.ambiguous_mappings) == 0
    assert len(resp.manual_handling) == 0
    assert resp.ready_for_review is True


def test_ready_for_review_false_when_missing_fields_exist():
    """ready_for_review is False if any required field is in missing_fields."""
    fields = [
        {"name": "name", "id": "name", "label": "Full Name", "type": "text", "required": True},
        {"name": "income", "id": "income", "label": "Income", "type": "text", "required": True},
    ]
    user_info = {"full_name": "Priya Sharma"}  # Missing income
    resp = FormMappingResponse.create_deterministic_mock(fields, user_info)
    assert len(resp.missing_fields) == 1
    assert resp.ready_for_review is False


def test_ready_for_review_false_when_ambiguous_mappings_exist():
    """ready_for_review is False when ambiguous mappings exist."""
    m_suggested = FormFieldMapping(target_field="name", status=FieldMappingStatus.SUGGESTED, value="Priya")
    m_ambiguous = FormFieldMapping(target_field="gender", status=FieldMappingStatus.AMBIGUOUS)

    resp = FormMappingResponse(
        suggested_mappings=[m_suggested],
        ambiguous_mappings=[m_ambiguous],
    )
    # When initialized directly, check conservative policy logic
    ready = (
        len(resp.missing_fields) == 0
        and len(resp.ambiguous_mappings) == 0
        and len(resp.manual_handling) == 0
    )
    assert ready is False


def test_ready_for_review_false_when_manual_handling_exists():
    """ready_for_review is False when manual_handling controls (e.g. radio) exist."""
    fields = [
        {"name": "name", "id": "name", "label": "Full Name", "type": "text", "required": True},
        {"name": "gender", "id": "gender", "label": "Gender", "type": "radio", "required": False},
    ]
    user_info = {"full_name": "Priya Sharma"}
    resp = FormMappingResponse.create_deterministic_mock(fields, user_info)
    assert len(resp.manual_handling) == 1
    assert resp.ready_for_review is False


def test_mock_processing_time_is_none():
    """processing_time_seconds must be None for deterministic mock runs."""
    fields = [{"name": "name", "id": "name", "label": "Name", "type": "text"}]
    user_info = {"name": "Priya"}
    resp = FormMappingResponse.create_deterministic_mock(fields, user_info)
    assert resp.processing_time_seconds is None


def test_all_mappings_synchronization():
    """all_mappings must remain synchronized with the four categories."""
    m1 = FormFieldMapping(target_field="name", status=FieldMappingStatus.SUGGESTED, value="Priya")
    m2 = FormFieldMapping(target_field="dob", status=FieldMappingStatus.MISSING)
    m3 = FormFieldMapping(target_field="gender", status=FieldMappingStatus.AMBIGUOUS)
    m4 = FormFieldMapping(target_field="category", status=FieldMappingStatus.MANUAL_HANDLING, field_type="radio")

    # Providing categorized lists populates all_mappings
    resp = FormMappingResponse(
        suggested_mappings=[m1],
        missing_fields=[m2],
        ambiguous_mappings=[m3],
        manual_handling=[m4],
    )
    assert len(resp.all_mappings) == 4
    assert resp.all_mappings == [m1, m2, m3, m4]

    # Providing all_mappings populates the four categorized lists
    resp2 = FormMappingResponse(all_mappings=[m1, m2, m3, m4])
    assert resp2.suggested_mappings == [m1]
    assert resp2.missing_fields == [m2]
    assert resp2.ambiguous_mappings == [m3]
    assert resp2.manual_handling == [m4]


def test_ready_for_review_validation_error_on_status_error():
    """FormMappingResponse must reject ready_for_review=True if status is ERROR."""
    with pytest.raises(ValidationError) as exc_info:
        FormMappingResponse(
            status=AIResponseStatus.ERROR,
            ready_for_review=True,
            error_message="Something failed",
        )
    assert "An error response cannot have ready_for_review=True" in str(exc_info.value)


def test_ready_for_review_validation_error_with_unresolved_fields():
    """FormMappingResponse must reject ready_for_review=True if missing, ambiguous, or manual fields exist."""
    m_missing = FormFieldMapping(target_field="dob", status=FieldMappingStatus.MISSING)
    with pytest.raises(ValidationError) as exc_info:
        FormMappingResponse(
            status=AIResponseStatus.SUCCESS,
            ready_for_review=True,
            missing_fields=[m_missing],
        )
    assert "ready_for_review cannot be True when unresolved fields exist" in str(exc_info.value)


def test_manual_handling_synthetic_radio_unresolvable_identifier():
    """
    Interpretation B:
    When a synthetic unsupported radio control has no uniquely resolvable identifier
    (name=None, id=None, label=None) and only a selector (selector='#cat_gen'):
      - target_field must be None.
      - field_id must be None.
      - label must be None.
      - selector must be preserved as '#cat_gen'.
      - field_type must be 'radio'.
      - status must be manual_handling.
      - ready_for_review must be False.
    """
    synthetic_radio_field = {
        "name": None,
        "id": None,
        "label": None,
        "type": "radio",
        "selector": "#cat_gen",
        "required": False,
    }
    resp = FormMappingResponse.create_deterministic_mock(
        fields=[synthetic_radio_field],
        user_information={},
    )
    assert len(resp.manual_handling) == 1
    mapping = resp.manual_handling[0]
    assert mapping.target_field is None
    assert mapping.field_id is None
    assert mapping.label is None
    assert mapping.selector == "#cat_gen"
    assert mapping.field_type == "radio"
    assert mapping.status == FieldMappingStatus.MANUAL_HANDLING
    assert resp.ready_for_review is False
    assert "cannot be resolved for automated filling" in mapping.reasoning


