# [ARCHIVED] IMPLEMENTATION PLAN: Factur-X API (v1.0.0)

> **STATUS: COMPLETED** (2026-01-17)
> This plan was executed for the v1.0.0 release. See `NEXT_STEPS.md` for future plans.

## 1. Objective

Build a stateless, developer-first REST API to:

1. Convert standard PDFs + JSON metadata into **Factur-X (ZUGFeRD 2.2)** hybrid invoices (PDF/A-3).
2. Validate PDF or XML files against **EN 16931** standards.

## 2. Technical Stack

- **Language**: Python 3.11+
- **Framework**: FastAPI
- **Core Libraries**:
  - `factur-x`: For embedding XML into PDF (PDF/A-3 generation) and extraction.
  - `xmlschema`: For strict XML validation against XSDs.
  - `jinja2`: For robust and flexible generation of XML from JSON input.
  - `pypdf`: Underlying PDF manipulation (dependency of `factur-x`).
  - `uvicorn`: ASGI server.
  - `python-multipart`: For file handling.
- **Containerization**: Docker (optimized python-slim image).

## 3. Architecture

### Directory Structure

```
.
├── app/
│   ├── __init__.py
│   ├── main.py              # Application entry point
│   ├── api.py               # Route handlers
│   ├── services/
│   │   ├── generator.py     # XML Generation (Jinja2) & PDF Fusion (factur-x)
│   │   └── validator.py     # Validation logic (xmlschema)
│   ├── templates/
│   │   └── factur-x.xml.j2  # Jinja2 template for EN 16931 XML
│   └── schemas/
│       └── validation.py    # Pydantic models for API responses
├── Dockerfile
├── requirements.txt
└── tests/
    └── test_api.py
```

## 4. Endpoints Design

### `POST /v1/convert`

- **Input**: `multipart/form-data`
  - `pdf`: File (The original PDF invoice).
  - `metadata`: JSON string (Invoice details: Seller, Buyer, Line Items, Totals, etc.).
- **Process**:
    1. Validate input JSON against a Pydantic model (subset of EN 16931).
    2. Render the **Factur-X XML** using `jinja2` template + metadata.
    3. Use `factur-x` library (`generate_from_file` / `generate_from_bytes`) to embed the generated XML into the PDF.
    4. Ensure output is compliant PDF/A-3.
- **Output**: Streamed PDF file (`application/pdf`) with correct headers.
- **Error Handling**: Returns `400` if PDF invalid or JSON missing required fields.

### `POST /v1/validate`

- **Input**: `multipart/form-data`
  - `file`: File (XML or PDF).
- **Process**:
    1. Detect file type (MIME/Extension).
    2. If PDF: Extract XML using `factur-x.get_facturx_xml_from_pdf()`.
    3. If XML: Use raw content.
    4. Validate XML using `xmlschema` against bundled **EN 16931** XSD.
- **Output**: JSON Report

    ```json
    {
      "valid": true,
      "format": "factur-x",
      "flavor": "en16931",
      "errors": []
    }
    ```

## 5. Development Strategy

1. **Setup**: Initialize environment and dependencies.
2. **Core Implementation**:
    - Create `generator.py` with the Jinja2 rendering logic.
    - Implement the `factur-x` integration.
    - Implement the `xmlschema` validation (we will download the official XSDs).
3. **API Layer**: Connect logic to FastAPI endpoints.
4. **Testing**:
    - Unit tests for XML generation.
    - Integration tests for the full Convert -> Validate loop.
    - Generate `TEST_REPORT.md` artifact.
5. **Dockerization**: Create Dockerfile.

## 6. Verification

- **Validation**: The `v1/validate` endpoint will be used to verify the output of `v1/convert` during testing.
- **Compliance**: Ensure "Alternative" relationship in PDF metadata (handled by `factur-x` lib).

## 7. Next Steps

- Approve this plan to begin coding.
