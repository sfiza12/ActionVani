"""
ActionVani – Speech Transcription Mock.

Deterministic mock implementation of transcribe_audio() for offline testing
and architectural contract validation.

Contract:
    transcribe_audio(audio_path: str) -> dict

Rules:
    - Returns TranscriptionResponse-compliant dict with is_mock=True.
    - Sets confidence=None and processing_time_seconds=None (never fabricated).
    - Validates audio_path is a non-empty string.
    - Does NOT read, modify, or delete the original audio file.
    - Does NOT load any AI model or perform real inference.
"""

import os
from typing import Any, Dict

from backend.ai.common.schemas import (
    AIResponseStatus,
    SupportedLanguage,
    TranscriptionResponse,
)
from backend.ai.common.exceptions import AIFileError, AIInputError


# Deterministic mock transcripts keyed by file extension and basename patterns.
# These are fixed sample strings for testing; they do NOT represent real speech.
_MOCK_TRANSCRIPTS: Dict[str, Dict[str, str]] = {
    "hi": {
        "text": "मुझे सरकारी छात्रवृत्ति के लिए आवेदन करना है।",
        "description": "Mock Hindi transcript: citizen requesting scholarship application.",
    },
    "kn": {
        "text": "ನನಗೆ ಸರ್ಕಾರಿ ವಿದ್ಯಾರ್ಥಿವೇತನಕ್ಕೆ ಅರ್ಜಿ ಸಲ್ಲಿಸಬೇಕು.",
        "description": "Mock Kannada transcript: citizen requesting scholarship application.",
    },
    "en": {
        "text": "I want to apply for a government scholarship.",
        "description": "Mock English transcript: citizen requesting scholarship application.",
    },
}

# File extension to language hint mapping (deterministic heuristic for mock only)
_EXTENSION_LANGUAGE_HINTS: Dict[str, str] = {
    ".hi.wav": "hi",
    ".hi.mp3": "hi",
    ".hi.mp4": "hi",
    ".hin.wav": "hi",
    ".hin.mp3": "hi",
    ".hin.mp4": "hi",
    ".kn.wav": "kn",
    ".kn.mp3": "kn",
    ".kn.mp4": "kn",
    ".kan.wav": "kn",
    ".kan.mp3": "kn",
    ".kan.mp4": "kn",
}


def _detect_mock_language(audio_path: str) -> SupportedLanguage:
    """
    Deterministic language detection from filename patterns.

    Priority:
        1. Known language-specific filename suffixes (e.g. 'hin_audio.mp4').
        2. 'hindi', 'kannada' substrings in the path.
        3. Default to English.
    """
    lower_path = audio_path.lower()

    # Check extension-based patterns
    for suffix, lang_code in _EXTENSION_LANGUAGE_HINTS.items():
        if lower_path.endswith(suffix):
            return SupportedLanguage.normalize(lang_code)

    # Check directory or filename substring patterns
    if "hindi" in lower_path or "hin" in lower_path or "/hi/" in lower_path:
        return SupportedLanguage.HI
    if "kannada" in lower_path or "kan" in lower_path or "/kn/" in lower_path:
        return SupportedLanguage.KN

    return SupportedLanguage.EN


def transcribe_audio(audio_path: str) -> dict:
    """
    Deterministic mock implementation of speech transcription.

    Args:
        audio_path: Path string to the audio file. Must be a non-empty string.
                    The file is NOT actually read or opened.

    Returns:
        dict: TranscriptionResponse-compliant dictionary with is_mock=True,
              confidence=None, and processing_time_seconds=None.

    Raises:
        AIInputError: If audio_path is not a non-empty string.
        AIFileError: If audio_path has an unsupported extension.
    """
    # --- Input Validation ---
    if not isinstance(audio_path, str) or not audio_path.strip():
        raise AIInputError(
            message="audio_path must be a non-empty string.",
            details={"parameter": "audio_path"},
        )

    clean_path = audio_path.strip()

    # Validate file extension (mock only checks extension, not actual file)
    supported_extensions = (".wav", ".mp3", ".mp4", ".flac", ".ogg", ".webm", ".m4a")
    _, ext = os.path.splitext(clean_path.lower())
    if ext not in supported_extensions:
        raise AIFileError(
            message=f"Unsupported audio file extension '{ext}'. Supported: {', '.join(supported_extensions)}.",
            details={"extension": ext, "supported": list(supported_extensions)},
        )

    # --- Deterministic Mock Response ---
    detected_language = _detect_mock_language(clean_path)
    lang_code = detected_language.value
    mock_data = _MOCK_TRANSCRIPTS.get(lang_code, _MOCK_TRANSCRIPTS["en"])

    response = TranscriptionResponse(
        status=AIResponseStatus.SUCCESS,
        text=mock_data["text"],
        language=detected_language,
        confidence=None,
        duration_seconds=None,
        processing_time_seconds=None,
        is_mock=True,
        error_message=None,
    )

    return response.model_dump()
