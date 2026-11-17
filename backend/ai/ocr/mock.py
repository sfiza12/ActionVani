"""
ActionVani – Document Extraction (OCR) Mock.

Deterministic mock implementation of extract_document_information() for offline
testing and architectural contract validation.

Contract:
    extract_document_information(document_path: str) -> dict

Rules:
    - Returns DocumentExtractionResponse-compliant dict with is_mock=True.
    - Sets confidence=None and processing_time_seconds=None (never fabricated).
    - Validates document_path is a non-empty string.
    - Does NOT read, modify, or delete the original document file.
    - Does NOT load any OCR engine or perform real extraction.
    - Uses deterministic sample extracted fields (not real PII).
"""

import os
from typing import Any, Dict

from backend.ai.common.schemas import (
    AIResponseStatus,
    DocumentExtractionResponse,
    DocumentType,
    ExtractedField,
)
from backend.ai.common.exceptions import AIFileError, AIInputError


# Supported document image/PDF extensions for mock validation
_SUPPORTED_DOC_EXTENSIONS = (".jpg", ".jpeg", ".png", ".bmp", ".tiff", ".tif", ".pdf", ".webp")

# Deterministic mock document type detection from filename keywords
_DOCTYPE_KEYWORD_MAP: list[tuple[list[str], DocumentType]] = [
    (["aadhaar", "aadhar", "uid"], DocumentType.AADHAAR),
    (["income", "income_cert"], DocumentType.INCOME_CERTIFICATE),
    (["caste", "caste_cert"], DocumentType.CASTE_CERTIFICATE),
    (["marks", "marksheet", "marks_card"], DocumentType.MARKS_CARD),
    (["ration", "ration_card"], DocumentType.RATION_CARD),
    (["bank", "passbook"], DocumentType.BANK_PASSBOOK),
]

# Deterministic mock extracted fields per document type.
# These are fixed sample values for contract validation; they are NOT real PII.
_MOCK_EXTRACTED_FIELDS: Dict[DocumentType, Dict[str, ExtractedField]] = {
    DocumentType.AADHAAR: {
        "full_name": ExtractedField(
            field_name="full_name",
            value="Sample Citizen Name",
            confidence=None,
        ),
        "date_of_birth": ExtractedField(
            field_name="date_of_birth",
            value="01/01/1990",
            confidence=None,
        ),
        "id_number": ExtractedField(
            field_name="id_number",
            value="XXXX XXXX 0000",
            confidence=None,
        ),
    },
    DocumentType.INCOME_CERTIFICATE: {
        "full_name": ExtractedField(
            field_name="full_name",
            value="Sample Citizen Name",
            confidence=None,
        ),
        "annual_income": ExtractedField(
            field_name="annual_income",
            value="250000",
            confidence=None,
        ),
        "issuing_authority": ExtractedField(
            field_name="issuing_authority",
            value="Tahsildar Office",
            confidence=None,
        ),
    },
    DocumentType.CASTE_CERTIFICATE: {
        "full_name": ExtractedField(
            field_name="full_name",
            value="Sample Citizen Name",
            confidence=None,
        ),
        "caste": ExtractedField(
            field_name="caste",
            value="Sample Category",
            confidence=None,
        ),
        "certificate_number": ExtractedField(
            field_name="certificate_number",
            value="CC-0000-0000",
            confidence=None,
        ),
    },
}

# Default mock fields for unrecognized document types
_DEFAULT_MOCK_FIELDS: Dict[str, ExtractedField] = {
    "full_name": ExtractedField(
        field_name="full_name",
        value="Sample Citizen Name",
        confidence=None,
    ),
}

# Mock extracted text per document type
_MOCK_EXTRACTED_TEXT: Dict[DocumentType, str] = {
    DocumentType.AADHAAR: (
        "Government of India\n"
        "Sample Citizen Name\n"
        "DOB: 01/01/1990\n"
        "XXXX XXXX 0000"
    ),
    DocumentType.INCOME_CERTIFICATE: (
        "Income Certificate\n"
        "Name: Sample Citizen Name\n"
        "Annual Income: Rs. 250000\n"
        "Issued by: Tahsildar Office"
    ),
    DocumentType.CASTE_CERTIFICATE: (
        "Caste Certificate\n"
        "Name: Sample Citizen Name\n"
        "Category: Sample Category\n"
        "Certificate No: CC-0000-0000"
    ),
}

_DEFAULT_MOCK_TEXT = "Document text extracted by OCR (mock).\nSample Citizen Name"


def _detect_document_type(document_path: str) -> DocumentType:
    """
    Deterministic document type detection from filename keywords.
    """
    lower_path = document_path.lower()
    for keywords, doc_type in _DOCTYPE_KEYWORD_MAP:
        for kw in keywords:
            if kw in lower_path:
                return doc_type
    return DocumentType.OTHER


def extract_document_information(document_path: str) -> dict:
    """
    Deterministic mock implementation of document information extraction.

    Args:
        document_path: Path string to the document file. Must be a non-empty string.
                       The file is NOT actually read or opened.

    Returns:
        dict: DocumentExtractionResponse-compliant dictionary with is_mock=True,
              confidence=None, and processing_time_seconds=None.

    Raises:
        AIInputError: If document_path is not a non-empty string.
        AIFileError: If document_path has an unsupported extension.
    """
    # --- Input Validation ---
    if not isinstance(document_path, str) or not document_path.strip():
        raise AIInputError(
            message="document_path must be a non-empty string.",
            details={"parameter": "document_path"},
        )

    clean_path = document_path.strip()

    # Validate file extension
    _, ext = os.path.splitext(clean_path.lower())
    if ext not in _SUPPORTED_DOC_EXTENSIONS:
        raise AIFileError(
            message=f"Unsupported document file extension '{ext}'. Supported: {', '.join(_SUPPORTED_DOC_EXTENSIONS)}.",
            details={"extension": ext, "supported": list(_SUPPORTED_DOC_EXTENSIONS)},
        )

    # --- Deterministic Mock Response ---
    doc_type = _detect_document_type(clean_path)
    extracted_fields = _MOCK_EXTRACTED_FIELDS.get(doc_type, _DEFAULT_MOCK_FIELDS)
    extracted_text = _MOCK_EXTRACTED_TEXT.get(doc_type, _DEFAULT_MOCK_TEXT)

    response = DocumentExtractionResponse(
        status=AIResponseStatus.SUCCESS,
        document_type=doc_type,
        extracted_text=extracted_text,
        extracted_fields=extracted_fields,
        unreadable_fields=[],
        requires_user_review=False,
        confidence=None,
        is_mock=True,
        processing_time_seconds=None,
        error_message=None,
    )

    return response.model_dump()
