# AutoCare ML Service

AutoCare ML Service is a modular system for extracting structured maintenance data from vehicle service photos using OCR and LLM technologies. The service processes images of maintenance records, recognizes text, extracts relevant fields, and outputs structured JSON data for further use.

## Overview

**Workflow:**

```txt
photo -> OCR -> text -> LLM -> JSON -> Database

photo -> Database (S3/MinIO)
```

1. **Photo Upload:** User submits a photo of a maintenance record.
2. **OCR Processing:** The image is processed by a chain of OCR handlers to extract text.
3. **LLM Extraction:** The recognized text is parsed by LLM-based extractors to identify key fields.
4. **Data Storage:** Extracted data is structured as JSON and stored in a database.

---

## OCR

OCR (Optical Character Recognition) is handled by a chain of modular handlers, each implementing a common interface. The chain allows for flexible processing and fallback between different OCR engines.

**Key Concepts:**

- **Handlers:** Each OCR handler implements `BaseOCRHandler` with a core `_process_image` method.
- **Methods:**
  - `process`: Runs OCR in a separate thread.
  - `should_skip`: Determines if the handler should process the image (e.g., image size limits).
  - `can_accept`: Validates the quality of the recognized text (e.g., confidence threshold).
- **Chaining:** If a handler cannot process or accept the result, the next handler in the chain is invoked.

**Supported OCR Engines:**

- **OCR Space:** External API (25k requests/month).
- **EasyOCR:** Local model loaded at runtime.
- **Tesseract:** Local OCR engine (ensure model is available).

---

## LLM Clients

LLM (Large Language Model) clients provide interfaces for extracting structured data from recognized text. They abstract the interaction with both external APIs and local models.

- **Interface:** Each client implements a `chat` method for communication.
- **Current Support:** DeepSeek API.
- **Planned:** Add compact local models (e.g., phi-2).

---

## Extractors

Extractors are responsible for parsing recognized text and extracting relevant fields.

- **Types:**
  - `BaseFieldExtractor`: Extracts a single field (useful for simple models or regex).
  - `BaseMultiFieldExtractor`: Extracts multiple fields at once.
- **Adapter:** `FieldToMultiAdapter` converts a list of single-field extractors into a multi-field extractor.
- **Strategies:** Support for different model selection strategies (local only, external only, fallback, hybrid).
- **Orchestration:** An orchestrator selects and runs the appropriate extractors based on strategy.

## Roadmap

- Add local phi-2 extractor support.
- Implement request timers for model calls.
- Add temporary or LRU caching for results.
- Improve Dockerfile with Tesseract and dependencies.
- Enhance LLM confidence calculation.
- Support time-based strategies for LLM API usage.
- Allow user confirmation or editing of extracted data.
- Use LLM for OCR text validation and correction.
- Add photo validation and throttling.
- Enrich extracted JSON with external data sources.
