"""
ActionVani – AI Module Configuration.

This module provides centralized, modular configuration for all AI submodules:
  - Speech Recognition (ASR)
  - Intent Classification
  - Form-Field Reasoning & Mapping
  - Document Extraction (OCR)

Key Architectural & Security Guarantees:
  - Configuration is read dynamically from environment variables when present.
  - No secrets, credentials, or API keys are hardcoded.
  - Model selection is fully configurable per environment.
  - Zero model downloading, weight loading, or pipeline initialization occurs
    during module import. Configuration objects remain lightweight data containers.
"""

from typing import Any, Dict, List, Optional
import os

# Safely attempt to load local .env files if python-dotenv is installed
try:
    from dotenv import load_dotenv

    load_dotenv()
except ImportError:
    pass

from pydantic import BaseModel, ConfigDict, Field


# ==============================================================================
# Helper Functions for Environment Variable Parsing
# ==============================================================================

def _get_env_str(key: str, default: str) -> str:
    """Retrieve string from environment or return default."""
    return os.getenv(key, default).strip()


def _get_env_bool(key: str, default: bool = False) -> bool:
    """Retrieve boolean from environment or return default."""
    val = os.getenv(key)
    if val is None:
        return default
    return val.strip().lower() in ("true", "1", "yes", "on")


def _get_env_int(key: str, default: int) -> int:
    """Retrieve integer from environment or return default."""
    val = os.getenv(key)
    if val is None:
        return default
    try:
        return int(val.strip())
    except ValueError:
        return default


def _get_env_float(key: str, default: float) -> float:
    """Retrieve float from environment or return default."""
    val = os.getenv(key)
    if val is None:
        return default
    try:
        return float(val.strip())
    except ValueError:
        return default


# ==============================================================================
# Submodule Configuration Models
# ==============================================================================

class SpeechConfig(BaseModel):
    """
    Configuration for vernacular Speech-to-Text (ASR) processing.
    """

    model_id: str = Field(
        default="openai/whisper-small",
        description="Hugging Face model ID or local directory path for the ASR model.",
    )
    fallback_model_id: Optional[str] = Field(
        default="openai/whisper-medium",
        description="Optional larger fallback model for challenging regional dialects (e.g. Kannada).",
    )
    device: str = Field(
        default="auto",
        description="Execution device: 'auto', 'cuda', or 'cpu'. Resolved on demand, never at import.",
    )
    sample_rate: int = Field(
        default=16000,
        description="Standard audio sample rate in Hz expected by the speech pipeline.",
    )
    timeout_seconds: float = Field(
        default=30.0,
        gt=0.0,
        description="Maximum execution time allowed for transcribing an audio clip.",
    )

    model_config = ConfigDict(frozen=False)


class IntentConfig(BaseModel):
    """
    Configuration for citizen intent classification and slot extraction.
    """

    model_id: str = Field(
        default="google/muril-base-cased",
        description="Hugging Face model ID for multilingual Indic intent classification.",
    )
    confidence_threshold: float = Field(
        default=0.6,
        ge=0.0,
        le=1.0,
        description="Minimum confidence score required to accept an intent without asking confirmation.",
    )
    timeout_seconds: float = Field(
        default=10.0,
        gt=0.0,
        description="Maximum allowed execution time for intent classification.",
    )

    model_config = ConfigDict(frozen=False)


class ReasoningConfig(BaseModel):
    """
    Configuration for LLM-based form-field reasoning and mapping.
    """

    model_id: str = Field(
        default="Qwen/Qwen2.5-1.5B-Instruct",
        description="Compact instruction-tuned model ID used for DOM field mapping.",
    )
    temperature: float = Field(
        default=0.1,
        ge=0.0,
        le=1.0,
        description="Sampling temperature for deterministic, structured form mapping.",
    )
    max_tokens: int = Field(
        default=1024,
        gt=0,
        description="Maximum token generation limit for reasoning output.",
    )
    timeout_seconds: float = Field(
        default=30.0,
        gt=0.0,
        description="Maximum reasoning latency allowed before falling back or timing out.",
    )

    model_config = ConfigDict(frozen=False)


class OCRConfig(BaseModel):
    """
    Configuration for document OCR and text extraction.
    """

    engine: str = Field(
        default="easyocr",
        description="OCR engine implementation identifier ('easyocr' or 'paddleocr').",
    )
    languages: List[str] = Field(
        default_factory=lambda: ["en", "hi", "kn"],
        description="List of language codes to load into the OCR reader.",
    )
    confidence_threshold: float = Field(
        default=0.5,
        ge=0.0,
        le=1.0,
        description="Minimum confidence score required for an extracted field.",
    )
    timeout_seconds: float = Field(
        default=30.0,
        gt=0.0,
        description="Maximum execution time allowed for document extraction.",
    )

    model_config = ConfigDict(frozen=False)


# ==============================================================================
# Central AI Master Configuration
# ==============================================================================

class AIConfig(BaseModel):
    """
    Centralized configuration master for the ActionVani AI module.

    Encapsulates all submodule configurations and provides safe accessors.
    """

    environment: str = Field(
        default="development",
        description="Operating environment: 'development', 'testing', or 'production'.",
    )
    use_mock_data: bool = Field(
        default=False,
        description="When True, AI modules return deterministic mock data without loading heavy models.",
    )
    default_language: str = Field(
        default="en",
        description="Default fallback regional language code ('en', 'hi', 'kn').",
    )
    supported_languages: List[str] = Field(
        default_factory=lambda: ["en", "hi", "kn"],
        description="List of all supported language codes for ActionVani.",
    )

    # Submodule configurations
    speech: SpeechConfig = Field(default_factory=SpeechConfig)
    intent: IntentConfig = Field(default_factory=IntentConfig)
    reasoning: ReasoningConfig = Field(default_factory=ReasoningConfig)
    ocr: OCRConfig = Field(default_factory=OCRConfig)

    # External service secrets (read from environment, NEVER hardcoded)
    bhashini_api_key: Optional[str] = Field(
        default=None,
        description="Optional API key for government Bhashini Indic speech services.",
    )
    openai_api_key: Optional[str] = Field(
        default=None,
        description="Optional API key if using hosted OpenAI reasoning models.",
    )

    model_config = ConfigDict(frozen=False)

    def resolve_device(self) -> str:
        """
        Lazily resolves the target hardware device ('cuda' or 'cpu').

        Guarantees that PyTorch or CUDA checks are only performed when explicitly
        requested at runtime, and NEVER upon importing this configuration module.

        Returns:
            str: 'cuda' if GPU is available and requested, otherwise 'cpu'.
        """
        configured = self.speech.device.lower().strip()
        if configured in ("cuda", "cpu"):
            return configured

        # If configured as 'auto', safely check PyTorch CUDA availability on demand
        try:
            import torch

            return "cuda" if torch.cuda.is_available() else "cpu"
        except ImportError:
            return "cpu"

    def to_safe_dict(self) -> Dict[str, Any]:
        """
        Return a dictionary of the configuration with sensitive API keys redacted.
        Safe for logging, debug endpoints, and status inspections.
        """
        data = self.model_dump()
        if data.get("bhashini_api_key"):
            data["bhashini_api_key"] = "[REDACTED]"
        if data.get("openai_api_key"):
            data["openai_api_key"] = "[REDACTED]"
        return data


# ==============================================================================
# Central Factory & Singleton Provider
# ==============================================================================

def load_ai_config() -> AIConfig:
    """
    Construct an AIConfig instance initialized from environment variables with safe defaults.

    Returns:
        AIConfig: Fully initialized configuration instance.
    """
    return AIConfig(
        environment=_get_env_str("ACTIONVANI_ENV", "development"),
        use_mock_data=_get_env_bool("ACTIONVANI_AI_USE_MOCK", False),
        default_language=_get_env_str("ACTIONVANI_DEFAULT_LANGUAGE", "en"),
        supported_languages=["en", "hi", "kn"],
        speech=SpeechConfig(
            model_id=_get_env_str("ACTIONVANI_SPEECH_MODEL_ID", "openai/whisper-small"),
            fallback_model_id=_get_env_str("ACTIONVANI_SPEECH_FALLBACK_MODEL_ID", "openai/whisper-medium"),
            device=_get_env_str("ACTIONVANI_AI_DEVICE", "auto"),
            sample_rate=_get_env_int("ACTIONVANI_SPEECH_SAMPLE_RATE", 16000),
            timeout_seconds=_get_env_float("ACTIONVANI_SPEECH_TIMEOUT", 30.0),
        ),
        intent=IntentConfig(
            model_id=_get_env_str("ACTIONVANI_INTENT_MODEL_ID", "google/muril-base-cased"),
            confidence_threshold=_get_env_float("ACTIONVANI_INTENT_THRESHOLD", 0.6),
            timeout_seconds=_get_env_float("ACTIONVANI_INTENT_TIMEOUT", 10.0),
        ),
        reasoning=ReasoningConfig(
            model_id=_get_env_str("ACTIONVANI_REASONING_MODEL_ID", "Qwen/Qwen2.5-1.5B-Instruct"),
            temperature=_get_env_float("ACTIONVANI_REASONING_TEMP", 0.1),
            max_tokens=_get_env_int("ACTIONVANI_REASONING_MAX_TOKENS", 1024),
            timeout_seconds=_get_env_float("ACTIONVANI_REASONING_TIMEOUT", 30.0),
        ),
        ocr=OCRConfig(
            engine=_get_env_str("ACTIONVANI_OCR_ENGINE", "easyocr"),
            languages=["en", "hi", "kn"],
            confidence_threshold=_get_env_float("ACTIONVANI_OCR_THRESHOLD", 0.5),
            timeout_seconds=_get_env_float("ACTIONVANI_OCR_TIMEOUT", 30.0),
        ),
        bhashini_api_key=os.getenv("BHASHINI_API_KEY"),
        openai_api_key=os.getenv("OPENAI_API_KEY"),
    )


# Module-level default configuration instance (lightweight, zero model loads)
ai_config: AIConfig = load_ai_config()
