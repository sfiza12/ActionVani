"""
ActionVani – Mock Function Tests.

Comprehensive tests for all four deterministic mock functions:
    1. transcribe_audio(audio_path: str) -> dict
    2. classify_intent(transcript: str) -> dict
    3. process_form_fields(fields: list, user_information: dict) -> dict
    4. extract_document_information(document_path: str) -> dict

Coverage:
    - Successful outputs for all four mock functions.
    - Invalid input handling and correct exception types.
    - All form mapping categories (suggested, missing, ambiguous, manual_handling).
    - Unsupported controls (radio, select-multiple) flagged for manual handling.
    - all_mappings consistency with categorized lists.
    - ready_for_review safety invariants.
    - is_mock, confidence=None, processing_time_seconds=None enforcement.
    - Schema compliance via Pydantic model_validate().
"""

import sys
import os
from pathlib import Path

# Ensure repository root is on sys.path for imports
_REPO_ROOT = str(Path(__file__).resolve().parents[3])
if _REPO_ROOT not in sys.path:
    sys.path.insert(0, _REPO_ROOT)

import pytest

from backend.ai.common.schemas import (
    AIResponseStatus,
    AgreedIntent,
    DocumentType,
    FieldMappingStatus,
    FormMappingResponse,
    IntentClassificationResponse,
    TranscriptionResponse,
    DocumentExtractionResponse,
)
from backend.ai.common.exceptions import AIFileError, AIInputError

from backend.ai.speech.mock import transcribe_audio
from backend.ai.intent.mock import classify_intent
from backend.ai.reasoning.mock import process_form_fields
from backend.ai.ocr.mock import extract_document_information


# ==============================================================================
# 1. transcribe_audio() Tests
# ==============================================================================

class TestTranscribeAudio:
    """Tests for the speech transcription mock function."""

    def test_successful_english_transcription(self):
        """English audio path produces a valid mock transcription."""
        result = transcribe_audio("uploads/audio/sample_en.wav")
        assert result["status"] == "success"
        assert result["is_mock"] is True
        assert result["confidence"] is None
        assert result["processing_time_seconds"] is None
        assert result["error_message"] is None
        assert isinstance(result["text"], str)
        assert len(result["text"]) > 0

    def test_successful_hindi_transcription(self):
        """Hindi audio path detects Hindi language and returns Hindi text."""
        result = transcribe_audio("datasets/audio/hindi/hin_audio.mp4")
        assert result["language"] == "hi"
        assert result["is_mock"] is True
        assert result["confidence"] is None

    def test_successful_kannada_transcription(self):
        """Kannada audio path detects Kannada language."""
        result = transcribe_audio("datasets/audio/kannada/kan_sample.wav")
        assert result["language"] == "kn"
        assert result["is_mock"] is True

    def test_schema_compliance(self):
        """Result validates against TranscriptionResponse Pydantic model."""
        result = transcribe_audio("test.wav")
        validated = TranscriptionResponse.model_validate(result)
        assert validated.is_mock is True
        assert validated.status == AIResponseStatus.SUCCESS

    def test_empty_path_raises_input_error(self):
        """Empty string raises AIInputError."""
        with pytest.raises(AIInputError):
            transcribe_audio("")

    def test_whitespace_path_raises_input_error(self):
        """Whitespace-only string raises AIInputError."""
        with pytest.raises(AIInputError):
            transcribe_audio("   ")

    def test_non_string_path_raises_input_error(self):
        """Non-string input raises AIInputError."""
        with pytest.raises(AIInputError):
            transcribe_audio(123)

    def test_none_path_raises_input_error(self):
        """None input raises AIInputError."""
        with pytest.raises(AIInputError):
            transcribe_audio(None)

    def test_unsupported_extension_raises_file_error(self):
        """Unsupported audio extension raises AIFileError."""
        with pytest.raises(AIFileError):
            transcribe_audio("document.txt")

    def test_unsupported_extension_exe_raises_file_error(self):
        """Executable file extension raises AIFileError."""
        with pytest.raises(AIFileError):
            transcribe_audio("malware.exe")

    def test_multiple_supported_extensions(self):
        """All supported audio extensions produce valid results."""
        for ext in (".wav", ".mp3", ".mp4", ".flac", ".ogg", ".webm", ".m4a"):
            result = transcribe_audio(f"audio/test{ext}")
            assert result["is_mock"] is True
            assert result["status"] == "success"


# ==============================================================================
# 2. classify_intent() Tests
# ==============================================================================

class TestClassifyIntent:
    """Tests for the intent classification mock function."""

    def test_scholarship_intent(self):
        """Scholarship keywords produce scholarship_application intent."""
        result = classify_intent("I want to apply for a government scholarship.")
        assert result["intent"] == "scholarship_application"
        assert result["is_mock"] is True
        assert result["confidence"] is None
        assert result["processing_time_seconds"] is None

    def test_scholarship_hindi_intent(self):
        """Hindi scholarship text produces correct intent."""
        result = classify_intent("मुझे सरकारी छात्रवृत्ति के लिए आवेदन करना है।")
        assert result["intent"] == "scholarship_application"

    def test_application_status_intent(self):
        """Status keywords produce application_status intent."""
        result = classify_intent("I want to check my application status.")
        assert result["intent"] == "application_status"

    def test_document_assistance_intent(self):
        """Document keywords produce document_assistance intent."""
        result = classify_intent("I need help uploading my certificate.")
        assert result["intent"] == "document_assistance"

    def test_eshram_intent(self):
        """E-Shram keywords produce eshram_registration intent."""
        result = classify_intent("I want to register on e-shram portal.")
        assert result["intent"] == "eshram_registration"
        assert result["target_scheme"] == "eshram"

    def test_government_service_intent(self):
        """Government service keywords produce general_government_service intent."""
        result = classify_intent("I need a government service.")
        assert result["intent"] == "general_government_service"

    def test_unknown_intent(self):
        """Unrecognizable text produces unknown intent."""
        result = classify_intent("Hello, how are you today?")
        assert result["intent"] == "unknown"
        assert result["is_mock"] is True

    def test_target_scheme_scholarship(self):
        """Scholarship intent returns target_scheme='ssp'."""
        result = classify_intent("Apply for post-matric scholarship.")
        assert result["target_scheme"] == "ssp"

    def test_schema_compliance(self):
        """Result validates against IntentClassificationResponse Pydantic model."""
        result = classify_intent("I want to apply for a scholarship.")
        validated = IntentClassificationResponse.model_validate(result)
        assert validated.is_mock is True
        assert validated.intent == AgreedIntent.SCHOLARSHIP_APPLICATION

    def test_empty_transcript_raises_input_error(self):
        """Empty string raises AIInputError."""
        with pytest.raises(AIInputError):
            classify_intent("")

    def test_whitespace_transcript_raises_input_error(self):
        """Whitespace-only string raises AIInputError."""
        with pytest.raises(AIInputError):
            classify_intent("   ")

    def test_non_string_transcript_raises_input_error(self):
        """Non-string input raises AIInputError."""
        with pytest.raises(AIInputError):
            classify_intent(42)

    def test_none_transcript_raises_input_error(self):
        """None input raises AIInputError."""
        with pytest.raises(AIInputError):
            classify_intent(None)


# ==============================================================================
# 3. process_form_fields() Tests
# ==============================================================================

class TestProcessFormFields:
    """Tests for the form-field mapping mock function."""

    # -- Fixture: Member 3's actual test_form.html fields --
    FIXTURE_FIELDS = [
        {"name": "name", "id": "name", "label": "Full Name", "type": "text", "selector": "#name", "required": True},
        {"name": "dob", "id": "dob", "label": "Date of Birth", "type": "date", "selector": "#dob", "required": True},
        {"name": "gender", "id": "gender", "label": "Gender", "type": "select", "selector": "#gender", "required": False},
        {"name": "agreement", "id": "agreement", "label": "I agree to the terms and conditions", "type": "checkbox", "selector": "#agreement", "required": False},
    ]

    def test_successful_mapping_with_fixture_fields(self):
        """All fixture fields with matching citizen data produce suggested mappings."""
        user_info = {"full_name": "Priya Sharma", "dob": "2001-08-15"}
        result = process_form_fields(self.FIXTURE_FIELDS, user_info)

        assert result["status"] == "success"
        assert result["is_mock"] is True
        assert result["confidence"] is None
        assert result["processing_time_seconds"] is None
        assert len(result["suggested_mappings"]) == 2

    def test_suggested_mapping_uses_real_target_field(self):
        """Suggested mappings use actual HTML name from DOM metadata."""
        user_info = {"full_name": "Priya Sharma"}
        fields = [self.FIXTURE_FIELDS[0]]  # name field
        result = process_form_fields(fields, user_info)

        mapping = result["suggested_mappings"][0]
        assert mapping["target_field"] == "name"
        assert mapping["field_id"] == "name"
        assert mapping["value"] == "Priya Sharma"
        assert mapping["status"] == "suggested"

    def test_missing_fields_for_unmatched_required(self):
        """Required fields without matching data appear in missing_fields."""
        user_info = {}  # No citizen data
        fields = [self.FIXTURE_FIELDS[0]]  # name field, required
        result = process_form_fields(fields, user_info)

        assert len(result["missing_fields"]) == 1
        missing = result["missing_fields"][0]
        assert missing["target_field"] == "name"
        assert missing["value"] is None
        assert missing["status"] == "missing"

    def test_unsupported_radio_in_manual_handling(self):
        """Radio controls are placed under manual_handling, not suggested."""
        radio_field = {
            "name": "gender", "id": "gender", "label": "Gender",
            "type": "radio", "selector": "#gender", "required": False,
        }
        result = process_form_fields([radio_field], {"gender": "male"})

        assert len(result["suggested_mappings"]) == 0
        assert len(result["manual_handling"]) == 1
        manual = result["manual_handling"][0]
        assert manual["target_field"] == "gender"
        assert manual["status"] == "manual_handling"
        assert manual["field_type"] == "radio"

    def test_unsupported_multiselect_in_manual_handling(self):
        """Multi-select controls are placed under manual_handling, not suggested."""
        multi_field = {
            "name": "subjects", "id": "subjects", "label": "Subjects",
            "type": "select-multiple", "selector": "#subjects", "required": False,
        }
        result = process_form_fields([multi_field], {"subjects": "math"})

        assert len(result["suggested_mappings"]) == 0
        assert len(result["manual_handling"]) == 1
        manual = result["manual_handling"][0]
        assert manual["field_type"] == "select-multiple"
        assert manual["status"] == "manual_handling"

    def test_unidentified_field_manual_handling(self):
        """Fields with no name, id, or label get target_field=None in manual_handling."""
        unidentified = {
            "name": None, "id": None, "label": None,
            "type": "text", "selector": "#mystery_field", "required": False,
        }
        result = process_form_fields([unidentified], {})

        assert len(result["manual_handling"]) == 1
        manual = result["manual_handling"][0]
        assert manual["target_field"] is None
        assert manual["field_id"] is None
        assert manual["selector"] == "#mystery_field"
        assert manual["status"] == "manual_handling"

    def test_all_mappings_consistency(self):
        """all_mappings equals the sum of all four categories."""
        user_info = {"full_name": "Priya Sharma"}
        radio_field = {
            "name": None, "id": None, "label": None,
            "type": "radio", "selector": "#cat_gen", "required": False,
        }
        fields = self.FIXTURE_FIELDS + [radio_field]
        result = process_form_fields(fields, user_info)

        total = (
            len(result["suggested_mappings"])
            + len(result["missing_fields"])
            + len(result["ambiguous_mappings"])
            + len(result["manual_handling"])
        )
        assert len(result["all_mappings"]) == total

    def test_ready_for_review_true_when_all_suggested(self):
        """ready_for_review is True when all fields have suggested mappings."""
        fields = [
            {"name": "name", "id": "name", "label": "Name", "type": "text", "required": True},
        ]
        user_info = {"full_name": "Priya Sharma"}
        result = process_form_fields(fields, user_info)

        assert result["ready_for_review"] is True
        assert len(result["missing_fields"]) == 0
        assert len(result["ambiguous_mappings"]) == 0
        assert len(result["manual_handling"]) == 0

    def test_ready_for_review_false_with_missing(self):
        """ready_for_review is False when missing_fields is non-empty."""
        fields = [
            {"name": "name", "id": "name", "label": "Name", "type": "text", "required": True},
        ]
        result = process_form_fields(fields, {})  # No matching data

        assert result["ready_for_review"] is False
        assert len(result["missing_fields"]) == 1

    def test_ready_for_review_false_with_manual_handling(self):
        """ready_for_review is False when manual_handling is non-empty."""
        radio_field = {
            "name": "category", "id": "category", "label": "Category",
            "type": "radio", "selector": "#category", "required": False,
        }
        result = process_form_fields([radio_field], {})

        assert result["ready_for_review"] is False
        assert len(result["manual_handling"]) == 1

    def test_schema_compliance(self):
        """Result validates against FormMappingResponse Pydantic model."""
        user_info = {"full_name": "Priya Sharma", "dob": "2001-08-15"}
        result = process_form_fields(self.FIXTURE_FIELDS, user_info)
        validated = FormMappingResponse.model_validate(result)
        assert validated.is_mock is True
        assert validated.confidence is None

    def test_non_list_fields_raises_input_error(self):
        """Non-list fields raises AIInputError."""
        with pytest.raises(AIInputError):
            process_form_fields("not a list", {})

    def test_non_dict_user_info_raises_input_error(self):
        """Non-dict user_information raises AIInputError."""
        with pytest.raises(AIInputError):
            process_form_fields([], "not a dict")

    def test_none_fields_raises_input_error(self):
        """None fields raises AIInputError."""
        with pytest.raises(AIInputError):
            process_form_fields(None, {})

    def test_none_user_info_raises_input_error(self):
        """None user_information raises AIInputError."""
        with pytest.raises(AIInputError):
            process_form_fields([], None)

    def test_empty_fields_returns_empty_response(self):
        """Empty fields list produces empty mappings with ready_for_review=True."""
        result = process_form_fields([], {})
        assert result["status"] == "success"
        assert result["is_mock"] is True
        assert len(result["suggested_mappings"]) == 0
        assert len(result["missing_fields"]) == 0
        assert len(result["ambiguous_mappings"]) == 0
        assert len(result["manual_handling"]) == 0
        assert result["ready_for_review"] is True

    def test_mock_confidence_always_none(self):
        """All individual mapping confidence values are None in mock mode."""
        user_info = {"full_name": "Priya Sharma"}
        result = process_form_fields(self.FIXTURE_FIELDS[:1], user_info)
        for mapping in result["all_mappings"]:
            assert mapping["confidence"] is None

    def test_canonical_serialization_keys(self):
        """Response dict uses canonical keys, not legacy aliases."""
        result = process_form_fields(self.FIXTURE_FIELDS, {"full_name": "Priya"})
        assert "suggested_mappings" in result
        assert "missing_fields" in result
        assert "ambiguous_mappings" in result
        assert "manual_handling" in result
        assert "all_mappings" in result
        assert "ready_for_review" in result
        # Legacy keys must NOT appear at the top level
        assert "suggested" not in result
        assert "missing" not in result
        assert "ambiguous" not in result


# ==============================================================================
# 4. extract_document_information() Tests
# ==============================================================================

class TestExtractDocumentInformation:
    """Tests for the document extraction mock function."""

    def test_successful_aadhaar_extraction(self):
        """Aadhaar card path produces aadhaar document type."""
        result = extract_document_information("uploads/aadhaar_card.jpg")
        assert result["status"] == "success"
        assert result["document_type"] == "aadhaar"
        assert result["is_mock"] is True
        assert result["confidence"] is None
        assert result["processing_time_seconds"] is None
        assert result["error_message"] is None

    def test_aadhaar_extracted_fields(self):
        """Aadhaar extraction produces expected mock fields."""
        result = extract_document_information("uploads/aadhaar_scan.png")
        fields = result["extracted_fields"]
        assert "full_name" in fields
        assert "id_number" in fields
        assert fields["full_name"]["field_name"] == "full_name"

    def test_income_certificate_extraction(self):
        """Income certificate path produces correct document type."""
        result = extract_document_information("docs/income_certificate.pdf")
        assert result["document_type"] == "income_certificate"
        assert result["is_mock"] is True

    def test_caste_certificate_extraction(self):
        """Caste certificate path produces correct document type."""
        result = extract_document_information("docs/caste_cert.jpg")
        assert result["document_type"] == "caste_certificate"

    def test_unknown_document_type(self):
        """Unrecognizable filename produces 'other' document type."""
        result = extract_document_information("uploads/random_document.png")
        assert result["document_type"] == "other"
        assert result["is_mock"] is True

    def test_extracted_text_present(self):
        """Extracted text is a non-empty string."""
        result = extract_document_information("uploads/aadhaar.jpg")
        assert isinstance(result["extracted_text"], str)
        assert len(result["extracted_text"]) > 0

    def test_raw_text_synchronized(self):
        """raw_text is synchronized with extracted_text."""
        result = extract_document_information("uploads/aadhaar.jpg")
        assert result["raw_text"] == result["extracted_text"]

    def test_schema_compliance(self):
        """Result validates against DocumentExtractionResponse Pydantic model."""
        result = extract_document_information("uploads/aadhaar.jpg")
        validated = DocumentExtractionResponse.model_validate(result)
        assert validated.is_mock is True
        assert validated.status == AIResponseStatus.SUCCESS

    def test_empty_path_raises_input_error(self):
        """Empty string raises AIInputError."""
        with pytest.raises(AIInputError):
            extract_document_information("")

    def test_whitespace_path_raises_input_error(self):
        """Whitespace-only string raises AIInputError."""
        with pytest.raises(AIInputError):
            extract_document_information("   ")

    def test_non_string_path_raises_input_error(self):
        """Non-string input raises AIInputError."""
        with pytest.raises(AIInputError):
            extract_document_information(42)

    def test_none_path_raises_input_error(self):
        """None input raises AIInputError."""
        with pytest.raises(AIInputError):
            extract_document_information(None)

    def test_unsupported_extension_raises_file_error(self):
        """Unsupported document extension raises AIFileError."""
        with pytest.raises(AIFileError):
            extract_document_information("document.docx")

    def test_unsupported_extension_txt_raises_file_error(self):
        """Text file extension raises AIFileError."""
        with pytest.raises(AIFileError):
            extract_document_information("notes.txt")

    def test_multiple_supported_extensions(self):
        """All supported document extensions produce valid results."""
        for ext in (".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".pdf", ".webp"):
            result = extract_document_information(f"document{ext}")
            assert result["is_mock"] is True
            assert result["status"] == "success"

    def test_unreadable_fields_empty_for_mock(self):
        """Mock extraction has no unreadable fields."""
        result = extract_document_information("uploads/aadhaar.jpg")
        assert result["unreadable_fields"] == []

    def test_requires_user_review_false_for_mock(self):
        """Mock extraction does not require user review."""
        result = extract_document_information("uploads/aadhaar.jpg")
        assert result["requires_user_review"] is False
