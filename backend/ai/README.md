# ActionVani – Member 4 AI Engine

## 1. Overview

The AI Engine is responsible for the intelligent processing components of ActionVani.

It consists of four main components:

- **Speech-to-Text:** Converts the user's voice into text.
- **Intent Classification:** Identifies the user's intention and requested government service.
- **LLM-Based Reasoning:** Understands user information and suggests mappings to actual government form fields.
- **OCR and Document Extraction:** Extracts information from uploaded documents.

The current implementation contains deterministic mock functions and shared Pydantic schemas. Real model inference is being developed separately.

## 2. Development Environment

Verified local development environment:

| Component | Configuration |
|---|---|
| Operating System | Windows |
| Python | 3.11.9 |
| GPU | NVIDIA GeForce RTX 4050 Laptop GPU |
| GPU Memory | 6 GB |
| PyTorch | 2.14.1+cu130 |
| CUDA | Available through PyTorch |
| Transformers | 5.23.0 |
| Ollama | 0.30.10 |

## 3. Python Environment Setup

Create a virtual environment from the repository root:

```powershell
python -m venv .venv
```

Activate it:

```powershell
.\.venv\Scripts\Activate.ps1
```

Install AI dependencies:

```powershell
python -m pip install -r backend/ai/requirements.txt
```

**Important:** CUDA-enabled PyTorch, Torchvision and Torchaudio must be installed separately using compatible versions. Do not replace the verified CUDA installation with a CPU-only build.

Verify GPU availability:

```powershell
python -c "import torch; print('CUDA:', torch.cuda.is_available()); print('GPU:', torch.cuda.get_device_name(0) if torch.cuda.is_available() else 'Not detected')"
```

## 4. Speech Recognition

Speech recognition uses the following libraries:

- Transformers
- PyTorch
- Torchaudio
- Librosa
- SoundFile
- SentencePiece

Whisper models are being evaluated for English, Hindi and Kannada speech recognition.

FFmpeg is installed separately and can be used to convert audio and video recordings into suitable audio formats.

Model compatibility and transcription accuracy must be evaluated separately for each language.

## 5. Intent Classification

Intent classification identifies the government service or action requested by the user.

The environment includes:

- Transformers
- PyTorch
- SentencePiece

Potential model architectures and checkpoints will be evaluated for multilingual intent classification.

The approved intent labels are:

- scholarship_application
- application_status
- document_assistance
- eshram_registration
- general_government_service
- unknown

## 6. LLM-Based Reasoning

Ollama is used to run local language models.

Verified local configuration:

| Property | Value |
|---|---|
| Ollama version | 0.30.10 |
| Model | llama3:latest |
| Architecture | Llama |
| Parameters | 8B |
| Quantization | Q4_0 |
| Model context metadata | 8192 |
| Python API | http://localhost:11434 |

Start or open the Ollama application and verify the model:

```powershell
ollama --version
ollama list
```

Test the Python connection:

```powershell
python -c "import requests; print(requests.get('http://localhost:11434/api/tags').status_code)"
```

The local Llama 3 model has successfully completed a basic Python inference experiment and generated parseable JSON.

The reasoning engine is responsible for:

- Matching user-provided information to actual form fields.
- Identifying missing information.
- Identifying ambiguous information.
- Generating clarification questions.
- Producing structured responses.

The LLM must not invent personal information or independently execute browser actions.

## 7. OCR and Document Processing

EasyOCR is used for text recognition from uploaded documents.

Separate multilingual reader configurations are required:

**English and Hindi:**

```python
import easyocr

reader_hi = easyocr.Reader(["en", "hi"], gpu=True)
```

**English and Kannada:**

```python
reader_kn = easyocr.Reader(["en", "kn"], gpu=True)
```

EasyOCR does not support combining English, Hindi and Kannada in a single reader configuration.

Document-processing libraries:

| Library | Purpose |
|---|---|
| EasyOCR | Text recognition |
| Pillow | Image processing |
| OpenCV | Image processing |
| PyPDF | Digital PDF text extraction |
| PyMuPDF | PDF page rendering |

Digital PDFs can be processed through text extraction. Scanned PDFs require page rendering followed by OCR.

Reader initialization has been verified. Actual recognition accuracy must still be tested using representative English, Hindi and Kannada documents.

## 8. AI Module Structure

```text
backend/
└── ai/
    ├── common/
    │   ├── config.py
    │   ├── exceptions.py
    │   └── schemas.py
    │
    ├── intent/
    │   ├── __init__.py
    │   └── mock.py
    │
    ├── ocr/
    │   ├── __init__.py
    │   └── mock.py
    │
    ├── reasoning/
    │   ├── __init__.py
    │   └── mock.py
    │
    ├── speech/
    │   ├── __init__.py
    │   └── mock.py
    │
    ├── tests/
    │   ├── test_mock_functions.py
    │   └── test_schemas.py
    │
    ├── requirements.txt
    └── README.md
```

## 9. Public AI Function Interfaces

The four agreed public interfaces are:

```python
transcribe_audio(audio_path: str) -> dict

classify_intent(transcript: str) -> dict

process_form_fields(fields: list, user_information: dict) -> dict

extract_document_information(document_path: str) -> dict
```

The response schemas are maintained in:

`backend/ai/common/schemas.py`

These interfaces and response schemas must remain compatible with Member 3's backend integration.

## 10. Backend Integration and Safety

- AI-generated field mappings must refer to actual identifiers supplied by the backend DOMExtractor.
- The backend independently validates mappings before FormFiller receives them.
- Unsupported controls must not be automatically filled.
- Missing and ambiguous information must be handled separately.
- User confirmation is required before final application submission.
- AI must not bypass CAPTCHA