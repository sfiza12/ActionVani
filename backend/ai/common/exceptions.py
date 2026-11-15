"""
ActionVani – AI Module Custom Exceptions.

This module defines specialized exception classes for all ActionVani AI
submodules: speech transcription, intent classification, form-field mapping,
and document extraction (OCR).

Security Notice:
    Citizens may share sensitive personal information (such as Aadhaar numbers,
    phone numbers, bank accounts, or application credentials) during interaction.
    Exception messages must NEVER include raw sensitive input values. All
    exceptions here provide safe default messages and automatic sanitization
    to prevent accidental credential or PII leakage into application logs.
"""

from typing import Any, Dict, Optional
import re


def sanitize_error_message(message: str) -> str:
    """
    Scrub potential sensitive data (e.g. Aadhaar, phone numbers) from error messages.

    Args:
        message (str): The raw error message string.

    Returns:
        str: Sanitized message string with sensitive tokens masked.
    """
    if not isinstance(message, str):
        return "An internal error occurred."

    # Redact 12-digit Aadhaar patterns (formatted or continuous)
    sanitized = re.sub(r"\b\d{4}[ -]?\d{4}[ -]?\d{4}\b", "[REDACTED_ID]", message)

    # Redact 10-digit Indian phone numbers
    sanitized = re.sub(r"\b[6-9]\d{9}\b", "[REDACTED_PHONE]", sanitized)

    # Redact key-value password or token patterns
    sanitized = re.sub(
        r"(?i)(password|token|secret|otp|aadhaar)\s*[:=]\s*['\"]?[^\s'\"]+['\"]?",
        r"\1=[REDACTED]",
        sanitized,
    )

    return sanitized


class AIError(Exception):
    """
    Base exception for all errors originating within the ActionVani AI module.

    Attributes:
        message (str): Safe, human-readable description of the error.
        error_code (str): Machine-readable identifier for client/API error reporting.
        details (Optional[Dict[str, Any]]): Optional non-sensitive contextual metadata.
    """

    def __init__(
        self,
        message: str = "An internal AI module error occurred.",
        error_code: str = "AI_GENERAL_ERROR",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        safe_message = sanitize_error_message(message)
        self.message: str = safe_message
        self.error_code: str = error_code
        self.details: Dict[str, Any] = details or {}
        super().__init__(self.message)

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize error details into a dictionary suitable for JSON responses.
        """
        return {
            "error_code": self.error_code,
            "message": self.message,
            "details": self.details,
        }

    def __str__(self) -> str:
        return f"[{self.error_code}] {self.message}"

    def __repr__(self) -> str:
        return f"{self.__class__.__name__}(error_code={self.error_code!r}, message={self.message!r})"


class AIInputError(AIError):
    """
    Raised when input supplied to an AI component is invalid, missing, or malformed.

    Typical causes:
        - An unsupported language code is provided (only 'en', 'hi', 'kn' supported).
        - An empty text string is passed to intent classification or form mapping.
        - Invalid parameters or conflicting argument structures are supplied.

    Security Guarantee:
        The invalid input value itself should not be echoed directly in the message.
    """

    def __init__(
        self,
        message: str = "Invalid or malformed input provided to the AI module.",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code="AI_INPUT_ERROR",
            details=details,
        )


class AIFileError(AIError):
    """
    Raised when an audio or document file cannot be found, read, opened,
    or has an unsupported media format.

    Typical causes:
        - The specified audio file path does not exist on disk.
        - A document image is corrupted or cannot be decoded by PIL/OpenCV.
        - An audio format or sample rate cannot be decoded by the audio loader.
    """

    def __init__(
        self,
        message: str = "Requested file could not be accessed, read, or decoded.",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code="AI_FILE_ERROR",
            details=details,
        )


class AIProcessingError(AIError):
    """
    Raised when an unexpected error occurs during AI model inference or pipeline execution.

    Typical causes:
        - A speech-to-text pipeline fails during acoustic or token decoding.
        - An OCR model crashes while scanning an image.
        - An LLM reasoning call fails due to runtime execution or context window issues.
    """

    def __init__(
        self,
        message: str = "An error occurred during AI inference or pipeline execution.",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code="AI_PROCESSING_ERROR",
            details=details,
        )


class AIModelUnavailableError(AIError):
    """
    Raised when a required AI model, weights checkpoint, or external AI service
    is unavailable, not installed, or cannot be loaded into memory.

    Typical causes:
        - Model weights are not found in the local cache and offline mode is active.
        - The requested hardware accelerator (e.g. 'cuda') is unavailable.
        - An external Indic speech or translation endpoint is offline or timed out.
    """

    def __init__(
        self,
        message: str = "The requested AI model or service is currently unavailable.",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code="AI_MODEL_UNAVAILABLE",
            details=details,
        )


class AIOutputValidationError(AIError):
    """
    Raised when the output produced by an AI model fails validation against
    the agreed Pydantic schema or required confidence constraints.

    Typical causes:
        - An LLM generated a form mapping referring to non-existent DOM field IDs.
        - An AI component produced confidence scores outside the valid 0.0 to 1.0 range.
        - A structured response is missing required keys or returned corrupted types.
    """

    def __init__(
        self,
        message: str = "AI model output failed schema validation or quality constraints.",
        details: Optional[Dict[str, Any]] = None,
    ) -> None:
        super().__init__(
            message=message,
            error_code="AI_OUTPUT_VALIDATION_ERROR",
            details=details,
        )
