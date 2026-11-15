"""
ActionVani – AI Module Schemas.

This module defines Pydantic v2 data models for all core AI capabilities:
  1. Speech Transcription (ASR)
  2. Intent Classification (Aligned with Member 3 Contract)
  3. Form-Field Reasoning & Mapping (Playwright DOM & FormFiller Compatible)
  4. Document Extraction (OCR Contract Restored)

Playwright & FormFiller Integration Rules (Member 3 Compatibility):
  - Canonical response categories: 'suggested_mappings', 'missing_fields', 'ambiguous_mappings', 'manual_handling'.
  - Backward compatibility aliases: 'suggested', 'missing', 'ambiguous'.
  - 'ready_for_review' indicates citizen review readiness (conservatively computed; NEVER authorizes submission).
    Enforced rule: ready_for_review cannot be True when status is ERROR, or when missing_fields, ambiguous_mappings,
    or manual_handling entries exist.
  - The Playwright DOM extractor supplies HTML field metadata: name, id, label, type, selector.
  - The FormFiller matches using actual field name, id, or label; it does NOT automatically
    understand semantic identifiers like 'applicant_name'.
  - Every suggested mapping must use 'target_field' containing an actual unique identifier
    from the supplied Playwright metadata (prefers HTML 'name', then 'id', then 'label').
  - AI MUST NEVER invent field identifiers or generate CSS selectors.
  - Target_field is mandatory and non-empty for 'suggested', 'missing', and 'ambiguous' mappings;
    it is optional (None) ONLY for 'manual_handling' mappings where no identifier exists.
  - FormFiller supports: 'text', 'date', 'select', 'checkbox'.
  - Controls with limitations ('radio', 'select-multiple') are flagged for manual handling
    or clarification and NEVER marked as ready-to-execute 'suggested' mappings.
  - Deterministic mock mappings set 'is_mock=True', 'confidence=None', and 'processing_time_seconds=None'
    without fabricating data or performance numbers.
"""

from enum import Enum
from typing import Any, Dict, List, Optional
from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator


# ==============================================================================
# Shared Enumerations & Types
# ==============================================================================

class SupportedLanguage(str, Enum):
    """
    Supported regional languages for ActionVani.

    Standard ISO-639-1 language codes:
      - 'en': English
      - 'hi': Hindi (हिन्दी)
      - 'kn': Kannada (ಕನ್ನಡ)
    """

    EN = "en"
    HI = "hi"
    KN = "kn"

    @classmethod
    def normalize(cls, value: Any) -> "SupportedLanguage":
        """
        Normalize language strings (e.g. 'english', 'Hindi', 'kn') to canonical enum.
        """
        if isinstance(value, cls):
            return value
        if isinstance(value, str):
            clean = value.strip().lower()
            mapping = {
                "en": cls.EN,
                "english": cls.EN,
                "hi": cls.HI,
                "hindi": cls.HI,
                "kn": cls.KN,
                "kannada": cls.KN,
            }
            if clean in mapping:
                return mapping[clean]
        raise ValueError(f"Unsupported language code '{value}'. Must be one of: 'en', 'hi', 'kn'.")


class AIResponseStatus(str, Enum):
    """
    Operational status of an AI component response.
    """

    SUCCESS = "success"
    PARTIAL = "partial"
    ERROR = "error"


# Supported & unsupported control types for Member 3's FormFiller
SUPPORTED_FORM_FILLER_TYPES: tuple[str, ...] = ("text", "date", "select", "checkbox")
UNSUPPORTED_FORM_FILLER_TYPES: tuple[str, ...] = (
    "radio",
    "radio-group",
    "select-multiple",
    "multi-select",
)


# ==============================================================================
# 1. Speech Transcription Schemas
# ==============================================================================

class TranscriptionRequest(BaseModel):
    """
    Request payload for converting spoken audio to text.
    """

    audio_path: Optional[str] = Field(
        default=None,
        description="Absolute or relative path to the audio file on disk.",
    )
    audio_bytes: Optional[bytes] = Field(
        default=None,
        description="Raw audio bytes in memory (e.g. from live microphone streaming).",
    )
    language: Optional[SupportedLanguage] = Field(
        default=None,
        description="Optional language hint ('en', 'hi', 'kn'). Auto-detected if omitted.",
    )

    @field_validator("language", mode="before")
    @classmethod
    def parse_language(cls, v: Any) -> Optional[SupportedLanguage]:
        if v is None:
            return None
        return SupportedLanguage.normalize(v)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "audio_path": "datasets/audio/hindi/hin_audio.mp4",
                "language": "hi",
            }
        }
    )


class TranscriptionResponse(BaseModel):
    """
    Response payload containing speech transcription results.
    """

    status: AIResponseStatus = Field(
        default=AIResponseStatus.SUCCESS,
        description="Operational status of speech recognition ('success', 'partial', 'error').",
    )
    text: str = Field(
        default="",
        description="Transcribed text output in the spoken regional language.",
    )
    language: Optional[SupportedLanguage] = Field(
        default=None,
        description="Detected or verified language code ('en', 'hi', 'kn').",
    )
    confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Confidence score between 0.0 and 1.0, or null if unavailable.",
    )
    duration_seconds: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Duration of the audio clip in seconds.",
    )
    processing_time_seconds: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Inference time taken to process the audio in seconds.",
    )
    is_mock: bool = Field(
        default=False,
        description="Explicit flag indicating whether this result is simulated mock/sample data.",
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error description if status is 'error', otherwise null.",
    )

    @field_validator("language", mode="before")
    @classmethod
    def parse_language(cls, v: Any) -> Optional[SupportedLanguage]:
        if v is None:
            return None
        return SupportedLanguage.normalize(v)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "success",
                "text": "मुझे सरकारी छात्रवृत्ति के लिए आवेदन करना है।",
                "language": "hi",
                "confidence": 0.94,
                "duration_seconds": 3.2,
                "processing_time_seconds": 1.48,
                "is_mock": False,
                "error_message": None,
            }
        }
    )


# ==============================================================================
# 2. Intent Classification Schemas (Aligned with Member 3 Contract)
# ==============================================================================

class AgreedIntent(str, Enum):
    """
    Agreed intent classifications matching Member 3's backend contract.
    """

    SCHOLARSHIP_APPLICATION = "scholarship_application"
    APPLICATION_STATUS = "application_status"
    DOCUMENT_ASSISTANCE = "document_assistance"
    ESHRAM_REGISTRATION = "eshram_registration"
    GENERAL_GOVERNMENT_SERVICE = "general_government_service"
    UNKNOWN = "unknown"


class IntentEntity(BaseModel):
    """
    Extracted entity or slot from a citizen's spoken utterance.
    """

    name: str = Field(
        description="Standardized name of the entity slot (e.g. 'scheme_name', 'state', 'annual_income').",
    )
    value: Any = Field(
        description="Extracted value of the entity slot.",
    )
    confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Extraction confidence between 0.0 and 1.0, or null.",
    )


class IntentClassificationRequest(BaseModel):
    """
    Request payload to classify intent and extract entities from text.
    """

    text: str = Field(
        min_length=1,
        description="Transcribed or typed citizen input text to classify.",
    )
    language: Optional[SupportedLanguage] = Field(
        default=None,
        description="Language code of the utterance ('en', 'hi', 'kn').",
    )

    @field_validator("language", mode="before")
    @classmethod
    def parse_language(cls, v: Any) -> Optional[SupportedLanguage]:
        if v is None:
            return None
        return SupportedLanguage.normalize(v)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "text": "I want to apply for a post-matric scholarship in Karnataka.",
                "language": "en",
            }
        }
    )


class IntentClassificationResponse(BaseModel):
    """
    Response payload identifying the citizen's goal and target government service.

    Aligns strictly with the agreed intent contract.
    """

    status: AIResponseStatus = Field(
        default=AIResponseStatus.SUCCESS,
        description="Operational status ('success', 'partial', 'error').",
    )
    intent: AgreedIntent = Field(
        default=AgreedIntent.UNKNOWN,
        description=(
            "Classified user intent matching Member 3's contract: "
            "'scholarship_application', 'application_status', 'document_assistance', "
            "'eshram_registration', 'general_government_service', 'unknown'."
        ),
    )
    target_scheme: Optional[str] = Field(
        default=None,
        description="Target public portal or welfare scheme (e.g. 'ssp', 'nsp', 'eshram').",
    )
    confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Classification confidence score between 0.0 and 1.0, or null.",
    )
    entities: Dict[str, Any] = Field(
        default_factory=dict,
        description="Dictionary of extracted entities and slot values.",
    )
    is_mock: bool = Field(
        default=False,
        description="Explicit flag indicating whether this result is simulated mock/sample data.",
    )
    processing_time_seconds: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Inference time in seconds.",
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error description if status is 'error', otherwise null.",
    )

    @field_validator("intent", mode="before")
    @classmethod
    def parse_intent(cls, v: Any) -> AgreedIntent:
        """
        Validate and normalize intent against the agreed contract.
        """
        if isinstance(v, AgreedIntent):
            return v
        if isinstance(v, str):
            clean = v.strip().lower()
            for item in AgreedIntent:
                if item.value == clean:
                    return item
        raise ValueError(
            f"Invalid intent '{v}'. Must be one of: {[i.value for i in AgreedIntent]}"
        )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "success",
                "intent": "scholarship_application",
                "target_scheme": "ssp",
                "confidence": 0.91,
                "entities": {
                    "scheme_category": "post_matric",
                    "state": "Karnataka",
                },
                "is_mock": False,
                "processing_time_seconds": 0.35,
                "error_message": None,
            }
        }
    )


# ==============================================================================
# 3. Form-Field Mapping Schemas (Playwright & FormFiller Compatible)
# ==============================================================================

class FieldMappingStatus(str, Enum):
    """
    Distinguishes the state of an individual form field mapping.

    Values:
      - 'suggested': High-confidence mapping for a FormFiller-supported control ready to execute.
      - 'missing': Mandatory form field lacks citizen information and must be asked via voice.
      - 'ambiguous': Conflicting candidate values or uncertain mapping requiring citizen clarification.
      - 'manual_handling': Unsupported control (e.g. radio group, multi-select) or unidentified field
        that cannot be reliably filled by FormFiller and must be handled manually or clarified with citizen.
    """

    SUGGESTED = "suggested"
    MISSING = "missing"
    AMBIGUOUS = "ambiguous"
    MANUAL_HANDLING = "manual_handling"


class FormFieldCandidate(BaseModel):
    """
    Represents an existing input field extracted by Member 3's Playwright DOM extractor.

    TARGET IDENTIFIER RULES:
      1. Prefers actual HTML 'name', then actual HTML 'id'.
      2. NEVER derives identifiers from CSS selectors (even when selector is '#name').
      3. Falls back to label only if both name and id are absent.
      4. If neither name, id, nor label exists, returns None (no identifier invented).
    """

    name: Optional[str] = Field(
        default=None,
        description="HTML name attribute from Playwright DOM metadata (e.g. 'name', 'dob').",
    )
    id: Optional[str] = Field(
        default=None,
        description="HTML id attribute from Playwright DOM metadata (e.g. 'name', 'dob').",
    )
    label: Optional[str] = Field(
        default=None,
        description="Visible label text associated with the form field (e.g. 'Full Name').",
    )
    type: str = Field(
        default="text",
        description="HTML input type: 'text', 'date', 'select', 'checkbox', 'radio', etc.",
    )
    selector: Optional[str] = Field(
        default=None,
        description="Exact CSS selector supplied by Playwright extractor (e.g. '#name'). Never generated by AI.",
    )
    required: bool = Field(
        default=False,
        description="Whether this field is mandatory for form submission.",
    )
    options: Optional[List[str]] = Field(
        default=None,
        description="Available choice options if the field is a select dropdown or radio group.",
    )
    value: Optional[Any] = Field(
        default=None,
        description="Current value in the DOM if already populated.",
    )

    @property
    def target_identifier(self) -> Optional[str]:
        """
        Return the preferred unique identifier for FormFiller matching.

        Resolution Priority:
          1. Actual HTML 'name' attribute.
          2. Actual HTML 'id' attribute.
          3. Actual form 'label' (for FormFiller label-based compatibility).

        Safety Constraints:
          - NEVER derives identifiers from CSS selectors.
          - NEVER synthesizes, guesses, or invents identifiers.
          - Returns None if neither name, id, nor label is available.
        """
        if self.name and self.name.strip():
            return self.name.strip()
        if self.id and self.id.strip():
            return self.id.strip()
        if self.label and self.label.strip():
            return self.label.strip()
        return None

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "name": "name",
                "id": "name",
                "label": "Full Name",
                "type": "text",
                "selector": "#name",
                "required": True,
                "options": None,
                "value": None,
            }
        }
    )


class FormFieldMapping(BaseModel):
    """
    Represents the mapping decision for a single portal DOM field.

    VALIDATION & COMPATIBILITY GUARANTEES:
      - 'target_field' is mandatory and non-empty for 'suggested', 'missing', and 'ambiguous' mappings.
      - 'target_field' is allowed to be None ONLY for 'manual_handling' mappings where no identifier exists.
      - 'field_id' is maintained as a synchronized backward-compatible alias.
      - If both 'target_field' and 'field_id' are provided, they MUST match.
      - Unsupported controls ('radio', 'select-multiple') are NEVER marked as 'suggested'.
      - Actual selector from Playwright metadata is preserved.
    """

    target_field: Optional[str] = Field(
        default=None,
        description=(
            "Actual unique identifier matching HTML name, id, or label from Playwright metadata. "
            "Mandatory for suggested, missing, and ambiguous mappings; optional only for manual_handling."
        ),
    )
    value: Optional[Any] = Field(
        default=None,
        description="The mapped value to populate. Null if missing, ambiguous, or requiring manual handling.",
    )
    status: FieldMappingStatus = Field(
        description="Distinguishes 'suggested', 'missing', 'ambiguous', or 'manual_handling'.",
    )
    field_type: Optional[str] = Field(
        default="text",
        description="Input element type from Playwright metadata (e.g. 'text', 'date', 'select', 'checkbox').",
    )
    selector: Optional[str] = Field(
        default=None,
        description="Exact selector from Playwright DOM metadata. Preserved as provided, never generated by AI.",
    )
    label: Optional[str] = Field(
        default=None,
        description="Field label from the form.",
    )
    confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Confidence score between 0.0 and 1.0, or null (used for deterministic mock mappings).",
    )
    reasoning: Optional[str] = Field(
        default=None,
        description="Human-readable explanation of why this mapping was chosen or why it requires manual handling.",
    )
    clarification_prompt: Optional[str] = Field(
        default=None,
        description="Voice prompt to ask the citizen if status is 'missing', 'ambiguous', or requires manual input.",
    )
    candidate_values: Optional[List[Any]] = Field(
        default=None,
        description="Candidate values when status is 'ambiguous'.",
    )
    field_id: Optional[str] = Field(
        default=None,
        description="Synchronized backward-compatible alias for target_field.",
    )

    @field_validator("target_field")
    @classmethod
    def validate_target_field_non_empty(cls, v: Optional[str]) -> Optional[str]:
        """Reject empty or whitespace-only target_field if a string is provided."""
        if v is not None:
            if not isinstance(v, str) or not v.strip():
                raise ValueError("target_field must not be empty or whitespace.")
            return v.strip()
        return None

    @model_validator(mode="before")
    @classmethod
    def validate_and_sync_identifiers(cls, data: Any) -> Any:
        """
        Validate target_field and field_id:
          - Reject empty strings.
          - If both are provided, validate that they match exactly.
          - Synchronize alias when only one is provided.
        """
        if isinstance(data, dict):
            target_field = data.get("target_field")
            field_id = data.get("field_id")

            # Check for empty string values
            if target_field is not None and isinstance(target_field, str) and not target_field.strip():
                raise ValueError("target_field must not be empty or whitespace.")
            if field_id is not None and isinstance(field_id, str) and not field_id.strip():
                raise ValueError("field_id must not be empty or whitespace.")

            # Validate that both match when both are present
            if target_field is not None and field_id is not None:
                if target_field.strip() != field_id.strip():
                    raise ValueError(
                        f"Conflicting identifiers: target_field='{target_field}' does not match "
                        f"field_id='{field_id}'. They must match."
                    )

            # Synchronize alias
            if target_field is None and field_id is not None:
                data["target_field"] = field_id.strip()
            elif target_field is not None and field_id is None:
                data["field_id"] = target_field.strip()

        return data

    @model_validator(mode="after")
    def validate_target_field_and_form_filler_support(self) -> "FormFieldMapping":
        """
        1. Ensure target_field is present and non-empty for suggested, missing, and ambiguous mappings.
           It is allowed to be None ONLY for manual_handling mappings where no identifier exists.
        2. Ensure unsupported controls (e.g. radio, select-multiple) are never marked
           as ready-to-execute 'suggested' mappings.
        """
        # Rule 1: target_field is mandatory for suggested, missing, and ambiguous mappings
        if self.status in (FieldMappingStatus.SUGGESTED, FieldMappingStatus.MISSING, FieldMappingStatus.AMBIGUOUS):
            if not self.target_field or not self.target_field.strip():
                raise ValueError(
                    f"target_field is mandatory and cannot be None or empty for '{self.status.value}' mappings."
                )

        # Rule 2: Unsupported controls cannot be suggested
        if self.field_type and self.field_type.lower().strip() in UNSUPPORTED_FORM_FILLER_TYPES:
            if self.status == FieldMappingStatus.SUGGESTED:
                raise ValueError(
                    f"Field type '{self.field_type}' is not supported by FormFiller for automated "
                    f"execution. It must be flagged as 'manual_handling' or 'ambiguous'."
                )
        return self

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "target_field": "name",
                "value": "Priya Sharma",
                "status": "suggested",
                "field_type": "text",
                "selector": "#name",
                "label": "Full Name",
                "confidence": None,
                "reasoning": "Matched citizen 'full_name' to Playwright fixture field name='name'.",
                "clarification_prompt": None,
                "candidate_values": None,
                "field_id": "name",
            }
        }
    )


class FormMappingRequest(BaseModel):
    """
    Request payload to map citizen details onto portal form fields.

    Accepts Playwright DOM fields and user_information dictionary.
    """

    fields: List[FormFieldCandidate] = Field(
        default_factory=list,
        description="List of fields extracted from the portal DOM by Member 3's Playwright extractor.",
    )
    user_information: Dict[str, Any] = Field(
        default_factory=dict,
        description="Dictionary of citizen-provided information collected from speech or documents.",
    )
    language: SupportedLanguage = Field(
        default=SupportedLanguage.EN,
        description="Language code for conversational clarification prompts ('en', 'hi', 'kn').",
    )

    @model_validator(mode="before")
    @classmethod
    def sync_aliases(cls, data: Any) -> Any:
        """
        Support backwards compatible field names ('form_fields' -> 'fields', 'user_data' -> 'user_information').
        """
        if isinstance(data, dict):
            if "fields" not in data and "form_fields" in data:
                data["fields"] = data["form_fields"]
            if "user_information" not in data and "user_data" in data:
                data["user_information"] = data["user_data"]
        return data

    @field_validator("language", mode="before")
    @classmethod
    def parse_language(cls, v: Any) -> SupportedLanguage:
        return SupportedLanguage.normalize(v)

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "fields": [
                    {
                        "name": "name",
                        "id": "name",
                        "label": "Full Name",
                        "type": "text",
                        "selector": "#name",
                        "required": True,
                    },
                    {
                        "name": "dob",
                        "id": "dob",
                        "label": "Date of Birth",
                        "type": "date",
                        "selector": "#dob",
                        "required": True,
                    },
                    {
                        "name": "gender",
                        "id": "gender",
                        "label": "Gender",
                        "type": "select",
                        "selector": "#gender",
                        "required": False,
                    },
                    {
                        "name": "agreement",
                        "id": "agreement",
                        "label": "I agree to the terms and conditions",
                        "type": "checkbox",
                        "selector": "#agreement",
                        "required": False,
                    },
                ],
                "user_information": {
                    "full_name": "Priya Sharma",
                },
                "language": "en",
            }
        }
    )


class FormMappingResponse(BaseModel):
    """
    Structured response containing categorized form-field mappings.

    CANONICAL FIELDS:
      - suggested_mappings: Confident values ready for FormFiller execution (text, date, select, checkbox).
      - missing_fields: Mandatory fields missing citizen data that must be asked via voice.
      - ambiguous_mappings: Multiple conflicting candidate values requiring citizen clarification.
      - manual_handling: Unsupported controls (e.g. radio groups, multi-select) or unresolvable fields.
      - ready_for_review: Conservative boolean indicating if details are ready for citizen review. Never authorizes submission.
        Strict rule: ready_for_review cannot be True when status is ERROR, or when missing_fields, ambiguous_mappings,
        or manual_handling entries exist.

    BACKWARD COMPATIBILITY:
      Provides 'suggested', 'missing', and 'ambiguous' properties and initializers
      so existing code continues functioning seamlessly.
    """

    status: AIResponseStatus = Field(
        default=AIResponseStatus.SUCCESS,
        description="Operational status ('success', 'partial', 'error').",
    )
    ready_for_review: bool = Field(
        default=False,
        description="Indicates whether the mapping result is ready to be presented to the citizen for review. It never authorizes form submission.",
    )
    suggested_mappings: List[FormFieldMapping] = Field(
        default_factory=list,
        description="Fields with confident values ready for FormFiller execution (text, date, select, checkbox).",
    )
    missing_fields: List[FormFieldMapping] = Field(
        default_factory=list,
        description="Mandatory fields missing citizen information that must be asked via voice.",
    )
    ambiguous_mappings: List[FormFieldMapping] = Field(
        default_factory=list,
        description="Fields with multiple conflicting candidate values requiring citizen clarification.",
    )
    manual_handling: List[FormFieldMapping] = Field(
        default_factory=list,
        description="Unsupported controls (e.g. radio groups, multi-select) or unidentified fields flagged for manual assistance.",
    )
    all_mappings: List[FormFieldMapping] = Field(
        default_factory=list,
        description="Consolidated list of all evaluated field mappings.",
    )
    confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Overall average confidence across all suggested mappings, or null.",
    )
    is_mock: bool = Field(
        default=False,
        description="Explicit flag indicating whether this result is simulated mock/sample data.",
    )
    processing_time_seconds: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Inference time in seconds, or null for deterministic mocks.",
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error description if status is 'error', otherwise null.",
    )

    # --------------------------------------------------------------------------
    # Backward Compatibility Aliases & Validators
    # --------------------------------------------------------------------------

    @model_validator(mode="before")
    @classmethod
    def sync_legacy_field_names(cls, data: Any) -> Any:
        """
        Support legacy field names ('suggested' -> 'suggested_mappings',
        'missing' -> 'missing_fields', 'ambiguous' -> 'ambiguous_mappings')
        during model initialization.
        """
        if isinstance(data, dict):
            if "suggested_mappings" not in data and "suggested" in data:
                data["suggested_mappings"] = data["suggested"]
            if "missing_fields" not in data and "missing" in data:
                data["missing_fields"] = data["missing"]
            if "ambiguous_mappings" not in data and "ambiguous" in data:
                data["ambiguous_mappings"] = data["ambiguous"]
        return data

    @property
    def suggested(self) -> List[FormFieldMapping]:
        """Backward-compatible property alias for suggested_mappings."""
        return self.suggested_mappings

    @suggested.setter
    def suggested(self, value: List[FormFieldMapping]) -> None:
        self.suggested_mappings = value

    @property
    def missing(self) -> List[FormFieldMapping]:
        """Backward-compatible property alias for missing_fields."""
        return self.missing_fields

    @missing.setter
    def missing(self, value: List[FormFieldMapping]) -> None:
        self.missing_fields = value

    @property
    def ambiguous(self) -> List[FormFieldMapping]:
        """Backward-compatible property alias for ambiguous_mappings."""
        return self.ambiguous_mappings

    @ambiguous.setter
    def ambiguous(self, value: List[FormFieldMapping]) -> None:
        self.ambiguous_mappings = value

    # --------------------------------------------------------------------------
    # List Synchronization & ready_for_review Safety Validator
    # --------------------------------------------------------------------------

    @model_validator(mode="after")
    def validate_ready_for_review_and_synchronize(self) -> "FormMappingResponse":
        """
        1. Enforce ready_for_review safety constraint:
           ready_for_review can NEVER be True when status is ERROR,
           or when unresolved fields exist in missing_fields, ambiguous_mappings, or manual_handling.
        2. Ensure categorized lists ('suggested_mappings', 'missing_fields', 'ambiguous_mappings', 'manual_handling')
           and 'all_mappings' remain consistent and synchronized.
        """
        has_categorized = bool(
            self.suggested_mappings
            or self.missing_fields
            or self.ambiguous_mappings
            or self.manual_handling
        )
        if self.all_mappings and not has_categorized:
            for m in self.all_mappings:
                if m.status == FieldMappingStatus.SUGGESTED:
                    self.suggested_mappings.append(m)
                elif m.status == FieldMappingStatus.MISSING:
                    self.missing_fields.append(m)
                elif m.status == FieldMappingStatus.AMBIGUOUS:
                    self.ambiguous_mappings.append(m)
                elif m.status == FieldMappingStatus.MANUAL_HANDLING:
                    self.manual_handling.append(m)
        elif has_categorized and not self.all_mappings:
            self.all_mappings = (
                self.suggested_mappings
                + self.missing_fields
                + self.ambiguous_mappings
                + self.manual_handling
            )

        # Enforce ready_for_review safety constraint
        if self.ready_for_review:
            if self.status == AIResponseStatus.ERROR:
                raise ValueError("An error response cannot have ready_for_review=True.")
            if self.missing_fields or self.ambiguous_mappings or self.manual_handling:
                raise ValueError(
                    "ready_for_review cannot be True when unresolved fields exist in "
                    "missing_fields, ambiguous_mappings, or manual_handling."
                )

        return self

    @classmethod
    def create_deterministic_mock(
        cls,
        fields: List[Any],
        user_information: Dict[str, Any],
        language: str = "en",
    ) -> "FormMappingResponse":
        """
        Create a deterministic mock mapping response without fabricating personal data.

        Safety & Contract Guarantees:
          - Uses ONLY citizen-provided information from user_information.
          - Never fabricates or synthesizes personal data (names, IDs, dates, income).
          - Sets confidence=None for all mock mappings.
          - Sets processing_time_seconds=None (no hardcoded measurements).
          - Sets ready_for_review conservatively: True ONLY when status is not ERROR and
            missing_fields, ambiguous_mappings, and manual_handling are all completely empty.
          - Flags unsupported controls (radio, select-multiple) for manual handling.
          - When a field has no name, id, or label: sets target_field=None, field_id=None,
            preserves selector separately, and flags as manual_handling (NO fabricated identifier).
          - Explicitly sets is_mock=True.

        Limitations of the Current Fixed Alias Map:
          The alias mapping below ('name' -> full_name/name/applicant_name, etc.) is a
          deterministic heuristic intended solely for offline testing, local fixtures,
          and architectural contract validation. It does NOT perform semantic reasoning
          or natural language inference. Any field not covered by these explicit aliases
          or exact key matches in user_information will remain unmapped (or flagged as
          missing if marked required), ensuring no unverified assumptions are made.
        """
        suggested_mappings: List[FormFieldMapping] = []
        missing_fields: List[FormFieldMapping] = []
        ambiguous_mappings: List[FormFieldMapping] = []
        manual_handling: List[FormFieldMapping] = []

        # Deterministic test fixture alias heuristic
        alias_map = {
            "name": ("name", "full_name", "applicant_name"),
            "dob": ("dob", "date_of_birth", "birth_date"),
            "gender": ("gender", "sex"),
            "agreement": ("agreement", "terms_agreed", "agreed"),
        }

        for raw_field in fields:
            if isinstance(raw_field, dict):
                candidate = FormFieldCandidate(**raw_field)
            elif isinstance(raw_field, FormFieldCandidate):
                candidate = raw_field
            else:
                continue

            target_id = candidate.target_identifier
            field_type = (candidate.type or "text").lower().strip()

            # If field has no valid identifier (neither name, id, nor label), it cannot be automated
            # Rule: Set target_field=None, field_id=None, preserve selector separately, status=manual_handling
            if not target_id:
                manual_handling.append(
                    FormFieldMapping(
                        target_field=None,
                        field_id=None,
                        value=None,
                        status=FieldMappingStatus.MANUAL_HANDLING,
                        field_type=field_type,
                        selector=candidate.selector,
                        label=candidate.label,
                        confidence=None,
                        reasoning="Field has neither HTML name, id, nor label; cannot be resolved for automated filling. Preserving selector separately without fabricated identifier.",
                        clarification_prompt="A form field could not be identified automatically. Please fill it manually on the portal.",
                    )
                )
                continue

            # Flag controls with FormFiller limitations
            if field_type in UNSUPPORTED_FORM_FILLER_TYPES:
                manual_handling.append(
                    FormFieldMapping(
                        target_field=target_id,
                        field_id=target_id,
                        value=None,
                        status=FieldMappingStatus.MANUAL_HANDLING,
                        field_type=field_type,
                        selector=candidate.selector,
                        label=candidate.label,
                        confidence=None,
                        reasoning=f"Control type '{field_type}' has limitations in FormFiller; flagged for manual selection.",
                        clarification_prompt=f"Please manually select the option for '{candidate.label or target_id}'.",
                    )
                )
                continue

            # Look for matching citizen data in user_information
            matched_value = None
            lookup_keys = alias_map.get(target_id.lower(), (target_id.lower(),))
            for key in lookup_keys:
                if key in user_information:
                    matched_value = user_information[key]
                    break

            if matched_value is not None:
                suggested_mappings.append(
                    FormFieldMapping(
                        target_field=target_id,
                        value=matched_value,
                        status=FieldMappingStatus.SUGGESTED,
                        field_type=field_type,
                        selector=candidate.selector,
                        label=candidate.label,
                        confidence=None,
                        reasoning=f"Matched citizen information to Playwright DOM field '{target_id}'.",
                    )
                )
            elif candidate.required:
                missing_fields.append(
                    FormFieldMapping(
                        target_field=target_id,
                        value=None,
                        status=FieldMappingStatus.MISSING,
                        field_type=field_type,
                        selector=candidate.selector,
                        label=candidate.label,
                        confidence=None,
                        reasoning=f"Mandatory field '{target_id}' is missing from citizen information.",
                        clarification_prompt=f"Please provide your {candidate.label or target_id}.",
                    )
                )

        # Conservative review policy: ready_for_review is True ONLY when
        # status is not ERROR, and there are NO missing fields, NO ambiguous mappings,
        # and NO manual_handling controls.
        status = AIResponseStatus.SUCCESS
        ready = (
            status != AIResponseStatus.ERROR
            and len(missing_fields) == 0
            and len(ambiguous_mappings) == 0
            and len(manual_handling) == 0
        )

        return cls(
            status=status,
            ready_for_review=ready,
            suggested_mappings=suggested_mappings,
            missing_fields=missing_fields,
            ambiguous_mappings=ambiguous_mappings,
            manual_handling=manual_handling,
            confidence=None,
            is_mock=True,
            processing_time_seconds=None,
        )

    model_config = ConfigDict(
        populate_by_name=True,
        json_schema_extra={
            "example": {
                "status": "success",
                "ready_for_review": False,
                "suggested_mappings": [
                    {
                        "target_field": "name",
                        "value": "Priya Sharma",
                        "status": "suggested",
                        "field_type": "text",
                        "selector": "#name",
                        "label": "Full Name",
                        "confidence": None,
                        "reasoning": "Matched citizen 'full_name' to Playwright fixture field name='name'.",
                        "clarification_prompt": None,
                        "candidate_values": None,
                        "field_id": "name",
                    }
                ],
                "missing_fields": [
                    {
                        "target_field": "dob",
                        "value": None,
                        "status": "missing",
                        "field_type": "date",
                        "selector": "#dob",
                        "label": "Date of Birth",
                        "confidence": None,
                        "reasoning": "Mandatory field 'dob' is missing from citizen information.",
                        "clarification_prompt": "Please provide your Date of Birth.",
                        "candidate_values": None,
                        "field_id": "dob",
                    }
                ],
                "ambiguous_mappings": [],
                "manual_handling": [],
                "all_mappings": [],
                "confidence": None,
                "is_mock": True,
                "processing_time_seconds": None,
                "error_message": None,
            }
        }
    )


# ==============================================================================
# 4. Document Extraction (OCR) Schemas (Contract Restored)
# ==============================================================================

class DocumentType(str, Enum):
    """
    Recognized identity and welfare certificate categories.
    """

    AADHAAR = "aadhaar"
    INCOME_CERTIFICATE = "income_certificate"
    CASTE_CERTIFICATE = "caste_certificate"
    MARKS_CARD = "marks_card"
    RATION_CARD = "ration_card"
    BANK_PASSBOOK = "bank_passbook"
    OTHER = "other"


class ExtractedField(BaseModel):
    """
    A single key-value field extracted from a scanned document.
    """

    field_name: str = Field(
        description="Standardized field name (e.g. 'full_name', 'date_of_birth', 'id_number').",
    )
    value: str = Field(
        description="Extracted text or numeric value from the document.",
    )
    confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Extraction confidence between 0.0 and 1.0, or null.",
    )
    bounding_box: Optional[List[float]] = Field(
        default=None,
        description="Coordinates of the bounding box [x1, y1, x2, y2] if available.",
    )

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "field_name": "full_name",
                "value": "Ramesh Kumar",
                "confidence": 0.95,
                "bounding_box": [120.0, 45.0, 310.0, 75.0],
            }
        }
    )


class DocumentExtractionRequest(BaseModel):
    """
    Request payload for document OCR and structured information extraction.
    """

    file_path: Optional[str] = Field(
        default=None,
        description="Local filesystem path to document image or PDF file.",
    )
    document_bytes: Optional[bytes] = Field(
        default=None,
        description="Raw document image bytes if provided directly in memory.",
    )
    document_type_hint: Optional[DocumentType] = Field(
        default=None,
        description="Optional hint of expected document category.",
    )
    language: Optional[SupportedLanguage] = Field(
        default=None,
        description="Expected language of text on the document ('en', 'hi', 'kn').",
    )

    @field_validator("language", mode="before")
    @classmethod
    def parse_language(cls, v: Any) -> Optional[SupportedLanguage]:
        if v is None:
            return None
        return SupportedLanguage.normalize(v)

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "file_path": "uploads/aadhaar_card.jpg",
                "document_type_hint": "aadhaar",
                "language": "en",
            }
        }
    )


class DocumentExtractionResponse(BaseModel):
    """
    Response payload containing structured fields and text extracted via OCR.

    Verification Disclaimer:
      OCR extracts visual text and numbers from uploaded document images.
      It DOES NOT verify or certify document authenticity, legal genuineness,
      or official government registry validity.
    """

    status: AIResponseStatus = Field(
        default=AIResponseStatus.SUCCESS,
        description="Operational status ('success', 'partial', 'error').",
    )
    document_type: DocumentType = Field(
        default=DocumentType.OTHER,
        description="Identified or classified document category (e.g. 'aadhaar', 'income_certificate').",
    )
    extracted_text: Optional[str] = Field(
        default=None,
        description="Full text extracted from the document by OCR.",
    )
    raw_text: Optional[str] = Field(
        default=None,
        description="Backward-compatible alias for extracted_text.",
    )
    extracted_fields: Dict[str, ExtractedField] = Field(
        default_factory=dict,
        description="Dictionary mapping standardized field names to extracted field details.",
    )
    unreadable_fields: List[str] = Field(
        default_factory=list,
        description="List of fields detected or expected but unreadable due to blur, damage, or degradation.",
    )
    requires_user_review: bool = Field(
        default=False,
        description="Flag indicating whether low confidence or unreadable sections require manual citizen review.",
    )
    confidence: Optional[float] = Field(
        default=None,
        ge=0.0,
        le=1.0,
        description="Average confidence across all extracted fields, or null.",
    )
    is_mock: bool = Field(
        default=False,
        description="Explicit flag indicating whether this result is simulated mock/sample data.",
    )
    processing_time_seconds: Optional[float] = Field(
        default=None,
        ge=0.0,
        description="Extraction duration in seconds.",
    )
    error_message: Optional[str] = Field(
        default=None,
        description="Error description if status is 'error', otherwise null.",
    )

    @model_validator(mode="before")
    @classmethod
    def sync_text_fields(cls, data: Any) -> Any:
        """
        Synchronize extracted_text and raw_text for backward compatibility.
        """
        if isinstance(data, dict):
            extracted = data.get("extracted_text")
            raw = data.get("raw_text")
            if extracted is None and raw is not None:
                data["extracted_text"] = raw
            elif extracted is not None and raw is None:
                data["raw_text"] = extracted
        return data

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "status": "success",
                "document_type": "aadhaar",
                "extracted_text": "Government of India\nRamesh Kumar\nDOB: 01/01/1990\nXXXX XXXX 1234",
                "raw_text": "Government of India\nRamesh Kumar\nDOB: 01/01/1990\nXXXX XXXX 1234",
                "extracted_fields": {
                    "full_name": {
                        "field_name": "full_name",
                        "value": "Ramesh Kumar",
                        "confidence": 0.95,
                        "bounding_box": [120.0, 45.0, 310.0, 75.0],
                    },
                    "id_number": {
                        "field_name": "id_number",
                        "value": "XXXX XXXX 1234",
                        "confidence": 0.92,
                        "bounding_box": [120.0, 100.0, 310.0, 130.0],
                    },
                },
                "unreadable_fields": [],
                "requires_user_review": False,
                "confidence": 0.935,
                "is_mock": False,
                "processing_time_seconds": 1.25,
                "error_message": None,
            }
        }
    )
