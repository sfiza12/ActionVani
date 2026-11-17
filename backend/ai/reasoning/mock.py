"""
ActionVani – Form-Field Reasoning Mock.

Deterministic mock implementation of process_form_fields() for offline testing
and architectural contract validation.

Contract:
    process_form_fields(fields: list, user_information: dict) -> dict

Playwright & FormFiller Integration Rules:
    - Uses ONLY real HTML field identifiers from the DOM extractor metadata.
    - NEVER invents field IDs, CSS selectors, or target_field values.
    - target_field resolution priority: HTML name → HTML id → label.
    - Unsupported controls (radio, select-multiple) are NEVER in suggested_mappings.
    - target_field is mandatory for suggested, missing, and ambiguous mappings;
      optional (None) ONLY for manual_handling where no identifier exists.
    - ready_for_review is strictly false if any unresolved category is non-empty.
    - Sets is_mock=True, confidence=None, processing_time_seconds=None.
    - Does NOT load any AI model or perform semantic reasoning.
"""

from typing import Any, Dict, List

from backend.ai.common.schemas import (
    FormFieldCandidate,
    FormMappingResponse,
)
from backend.ai.common.exceptions import AIInputError


def process_form_fields(fields: list, user_information: dict) -> dict:
    """
    Deterministic mock implementation of form-field mapping.

    Delegates to FormMappingResponse.create_deterministic_mock() which enforces
    all contract rules: identifier resolution, unsupported control handling,
    no-fabrication guarantees, and ready_for_review safety invariants.

    Args:
        fields: List of dicts or FormFieldCandidate objects representing DOM fields
                extracted by Member 3's Playwright DOM extractor.
        user_information: Dictionary of citizen-provided information.

    Returns:
        dict: FormMappingResponse-compliant dictionary with is_mock=True,
              confidence=None, and processing_time_seconds=None.

    Raises:
        AIInputError: If fields is not a list or user_information is not a dict.
    """
    # --- Input Validation ---
    if not isinstance(fields, list):
        raise AIInputError(
            message="fields must be a list of form field metadata dictionaries.",
            details={"parameter": "fields", "received_type": type(fields).__name__},
        )

    if not isinstance(user_information, dict):
        raise AIInputError(
            message="user_information must be a dictionary of citizen-provided data.",
            details={"parameter": "user_information", "received_type": type(user_information).__name__},
        )

    # --- Delegate to Approved Schema Mock ---
    response = FormMappingResponse.create_deterministic_mock(
        fields=fields,
        user_information=user_information,
    )

    return response.model_dump()
