"""
ActionVani – Intent Classification Mock.

Deterministic mock implementation of classify_intent() for offline testing
and architectural contract validation.

Contract:
    classify_intent(transcript: str) -> dict

Rules:
    - Returns IntentClassificationResponse-compliant dict with is_mock=True.
    - Sets confidence=None and processing_time_seconds=None (never fabricated).
    - Validates transcript is a non-empty string.
    - Maps intent deterministically using keyword matching (not AI inference).
    - Only produces intents from the agreed AgreedIntent enum.
    - Does NOT load any AI model.
"""

from typing import Any, Dict

from backend.ai.common.schemas import (
    AgreedIntent,
    AIResponseStatus,
    IntentClassificationResponse,
)
from backend.ai.common.exceptions import AIInputError


# Deterministic keyword → intent mapping for mock classification.
# Order matters: first match wins. Keywords are checked case-insensitively.
_INTENT_KEYWORD_MAP: list[tuple[list[str], AgreedIntent, str]] = [
    (
        ["scholarship", "छात्रवृत्ति", "ವಿದ್ಯಾರ್ಥಿವೇತನ", "post-matric", "pre-matric"],
        AgreedIntent.SCHOLARSHIP_APPLICATION,
        "ssp",
    ),
    (
        ["status", "track", "check application", "स्थिति", "ಸ್ಥಿತಿ"],
        AgreedIntent.APPLICATION_STATUS,
        None,
    ),
    (
        ["document", "certificate", "upload", "दस्तावेज़", "ದಾಖಲೆ", "aadhaar", "aadhar"],
        AgreedIntent.DOCUMENT_ASSISTANCE,
        None,
    ),
    (
        ["eshram", "e-shram", "labour", "labor", "ई-श्रम", "eshram_registration"],
        AgreedIntent.ESHRAM_REGISTRATION,
        "eshram",
    ),
    (
        ["government", "service", "portal", "सरकारी", "ಸರ್ಕಾರಿ", "apply"],
        AgreedIntent.GENERAL_GOVERNMENT_SERVICE,
        None,
    ),
]


def _match_intent(transcript: str) -> tuple[AgreedIntent, str | None]:
    """
    Deterministic keyword-based intent classification.

    Returns:
        Tuple of (matched_intent, target_scheme_or_None).
    """
    lower = transcript.lower()

    for keywords, intent, scheme in _INTENT_KEYWORD_MAP:
        for kw in keywords:
            if kw.lower() in lower:
                return intent, scheme

    return AgreedIntent.UNKNOWN, None


def classify_intent(transcript: str) -> dict:
    """
    Deterministic mock implementation of intent classification.

    Args:
        transcript: Transcribed or typed citizen text. Must be a non-empty string.

    Returns:
        dict: IntentClassificationResponse-compliant dictionary with is_mock=True,
              confidence=None, and processing_time_seconds=None.

    Raises:
        AIInputError: If transcript is not a non-empty string.
    """
    # --- Input Validation ---
    if not isinstance(transcript, str) or not transcript.strip():
        raise AIInputError(
            message="transcript must be a non-empty string.",
            details={"parameter": "transcript"},
        )

    clean_text = transcript.strip()

    # --- Deterministic Mock Classification ---
    intent, target_scheme = _match_intent(clean_text)

    response = IntentClassificationResponse(
        status=AIResponseStatus.SUCCESS,
        intent=intent,
        target_scheme=target_scheme,
        confidence=None,
        entities={},
        is_mock=True,
        processing_time_seconds=None,
        error_message=None,
    )

    return response.model_dump()
