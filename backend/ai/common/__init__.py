"""
ActionVani – AI Common Package.

Central schemas, exceptions, and configuration for the AI processing module.
"""

from backend.ai.common.config import (
    AIConfig,
    IntentConfig,
    OCRConfig,
    ReasoningConfig,
    SpeechConfig,
    ai_config,
    load_ai_config,
)
from backend.ai.common.exceptions import (
    AIError,
    AIFileError,
    AIInputError,
    AIModelUnavailableError,
    AIOutputValidationError,
    AIProcessingError,
    sanitize_error_message,
)
from backend.ai.common.schemas import (
    SUPPORTED_FORM_FILLER_TYPES,
    UNSUPPORTED_FORM_FILLER_TYPES,
    AgreedIntent,
    AIResponseStatus,
    DocumentExtractionRequest,
    DocumentExtractionResponse,
    DocumentType,
    ExtractedField,
    FieldMappingStatus,
    FormFieldCandidate,
    FormFieldMapping,
    FormMappingRequest,
    FormMappingResponse,
    IntentClassificationRequest,
    IntentClassificationResponse,
    IntentEntity,
    SupportedLanguage,
    TranscriptionRequest,
    TranscriptionResponse,
)

__all__ = [
    # Config
    "AIConfig",
    "SpeechConfig",
    "IntentConfig",
    "ReasoningConfig",
    "OCRConfig",
    "ai_config",
    "load_ai_config",
    # Exceptions
    "AIError",
    "AIInputError",
    "AIFileError",
    "AIProcessingError",
    "AIModelUnavailableError",
    "AIOutputValidationError",
    "sanitize_error_message",
    # Schemas - Common
    "SupportedLanguage",
    "AIResponseStatus",
    "SUPPORTED_FORM_FILLER_TYPES",
    "UNSUPPORTED_FORM_FILLER_TYPES",
    # Schemas - Speech
    "TranscriptionRequest",
    "TranscriptionResponse",
    # Schemas - Intent
    "AgreedIntent",
    "IntentEntity",
    "IntentClassificationRequest",
    "IntentClassificationResponse",
    # Schemas - Form Mapping
    "FieldMappingStatus",
    "FormFieldCandidate",
    "FormFieldMapping",
    "FormMappingRequest",
    "FormMappingResponse",
    # Schemas - OCR / Document
    "DocumentType",
    "ExtractedField",
    "DocumentExtractionRequest",
    "DocumentExtractionResponse",
]
