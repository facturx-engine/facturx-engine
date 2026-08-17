"""
FastAPI route handlers for Factur-X API.
"""
import json
import logging
import re
from io import BytesIO
from typing import Optional, Union

from fastapi import APIRouter, File, Form, HTTPException, UploadFile
from fastapi.responses import JSONResponse, StreamingResponse

from app.version import __version__

# Sanitize user-supplied values before injecting into HTTP headers
_UNSAFE_HEADER_RE = re.compile(r'[\r\n\x00-\x1f"\\]')

def _sanitize_header_value(name: str) -> str:
    """Strip characters unsafe for Content-Disposition header values."""
    return _UNSAFE_HEADER_RE.sub("_", name)[:200]

# Magic-byte signatures for supported file types
_PDF_MAGIC = b"%PDF-"
def _check_pdf_magic(content: bytes) -> bool:
    """Return True if content starts with the PDF magic bytes (%PDF-)."""
    return content[:5] == _PDF_MAGIC

def _check_xml_magic(content: bytes) -> bool:
    """Return True if content has an XML-like opening token.

    Namespace prefixes are caller-defined, so restricting this check to `rsm`
    or `ubl` would reject valid documents such as an unprefixed UBL `Invoice`.
    Secure parsing and format detection perform the authoritative checks later.
    """
    stripped = content.lstrip(b"\xef\xbb\xbf \t\r\n")  # strip UTF-8 BOM + whitespace
    return stripped.startswith(b"<?xml") or stripped.startswith(b"<")

from app.schemas.errors import ProblemDetails
from app.schemas.extraction import ExtractionResult
from app.schemas.integration import (
    SerializationDiagnostic,
    SerializationFailureResponse,
    SerializationResponse,
)
from app.schemas.validation import (
    InvoiceMetadata,
    ProValidationResult,
    SkippedLayer,
    ValidationResult,
)
from app.services.generator import GeneratorService
from app.services.pdf_utils import get_xml_from_pdf, is_pdfa3b
from app.services.validator import ValidationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1")


@router.post("/convert",
             tags=["Advanced Integration"],
             response_class=StreamingResponse,
             responses={
                 200: {"description": "Factur-X PDF successfully generated from provided PDF"},
                 400: {"model": ProblemDetails, "description": "Invalid input"},
                 500: {"model": ProblemDetails, "description": "Server error"}
             })
async def convert_to_facturx(
    pdf: UploadFile = File(..., description="Original PDF invoice (Bring Your Own PDF)"),
    metadata: str = Form(..., description="Invoice metadata as JSON")
):
    """
    Attach Factur-X/CII XML to an existing standard PDF invoice (BYOPDF).
    
    The input must be a valid PDF file (max upload size is controlled by MAX_UPLOAD_SIZE_MB, default 10MB). The API generates XML from metadata and embeds it into the PDF to create a Factur-X document. Use /v1/validate to verify final PDF/A status when needed.
    """
    import time

    from app.metrics import metrics
    start_time = time.time()
    metrics.inc("requests_total")
    metrics.inc("requests_convert")
    metrics.inc_gauge("active_requests")
    
    try:
        # Validate file extension (first pass)
        if not pdf.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail={"error": "INVALID_FILE_TYPE", "message": "Only PDF files are accepted"}
            )

        # Read PDF content (async I/O - avoids blocking the event loop)
        pdf_content = await pdf.read()
        if not pdf_content:
            raise HTTPException(
                status_code=400,
                detail={"error": "EMPTY_FILE", "message": "PDF file is empty"}
            )

        # Validate magic bytes (second pass - catches renamed non-PDF files)
        if not _check_pdf_magic(pdf_content):
            raise HTTPException(
                status_code=400,
                detail={"error": "INVALID_FILE_TYPE", "message": "File does not appear to be a valid PDF (bad magic bytes)"}
            )
        
        # Parse and validate metadata
        try:
            metadata_dict = json.loads(metadata)
            invoice_metadata = InvoiceMetadata(**metadata_dict)
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=400,
                detail={"error": "INVALID_JSON", "message": f"Invalid JSON in metadata: {str(e)}"}
            )
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail={"error": "INVALID_METADATA", "message": f"Invalid metadata structure: {str(e)}"}
            )
        
        # Generate Factur-X PDF
        try:
            facturx_pdf = GeneratorService.attach_xml_to_pdf(pdf_content, invoice_metadata)
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail={"error": "GENERATION_FAILED", "message": str(e)}
            )
        
        # Return as streaming response
        return StreamingResponse(
            BytesIO(facturx_pdf),
            media_type="application/pdf",
            headers={
                "Content-Disposition": f'attachment; filename="facturx_{_sanitize_header_value(invoice_metadata.invoice_number)}.pdf"'
            }
        )
        
    except HTTPException:
        metrics.inc("errors_total")
        raise
    except Exception as e:
        metrics.inc("errors_total")
        logger.exception(f"Unexpected error in convert endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "INTERNAL_ERROR", "message": "An unexpected error occurred"}
        )
    finally:
        metrics.dec_gauge("active_requests")
        metrics.observe("request_duration_seconds", time.time() - start_time)


@router.post("/xml",
             tags=["Core Workflows"],
             response_class=StreamingResponse,
             responses={
                 200: {"description": "Factur-X/CII XML successfully generated"},
                 400: {"model": ProblemDetails, "description": "Invalid input"},
                 500: {"model": ProblemDetails, "description": "Server error"}
             })
async def generate_facturx_xml(
    metadata: str = Form(..., description="Invoice metadata as JSON")
):
    """
    Generate the Factur-X/CII XML content directly from JSON metadata.
    
    This endpoint returns raw XML (Cross Industry Invoice D22B) 
    without the PDF wrapper.
    """
    import time

    from app.metrics import metrics
    start_time = time.time()
    metrics.inc("requests_total")
    metrics.inc("requests_xml")
    metrics.inc_gauge("active_requests")
    
    try:
        # Parse and validate metadata
        try:
            metadata_dict = json.loads(metadata)
            invoice_metadata = InvoiceMetadata(**metadata_dict)
        except json.JSONDecodeError as e:
            raise HTTPException(
                status_code=400,
                detail={"error": "INVALID_JSON", "message": f"Invalid JSON in metadata: {str(e)}"}
            )
        except Exception as e:
            raise HTTPException(
                status_code=400,
                detail={"error": "INVALID_METADATA", "message": f"Invalid metadata structure: {str(e)}"}
            )
        
        # Generate XML content
        try:
            xml_content = GeneratorService.generate_xml(invoice_metadata)
        except Exception as e:
            raise HTTPException(
                status_code=500,
                detail={"error": "GENERATION_FAILED", "message": str(e)}
            )
        
        # Return as streaming response
        return StreamingResponse(
            BytesIO(xml_content.encode('utf-8')),
            media_type="application/xml",
            headers={
                "Content-Disposition": f'attachment; filename="facturx_{_sanitize_header_value(invoice_metadata.invoice_number)}.xml"'
            }
        )
        
    except HTTPException:
        metrics.inc("errors_total")
        raise
    except Exception as e:
        metrics.inc("errors_total")
        logger.exception(f"Unexpected error in xml endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "INTERNAL_ERROR", "message": "An unexpected error occurred"}
        )
    finally:
        metrics.dec_gauge("active_requests")
        metrics.observe("request_duration_seconds", time.time() - start_time)


@router.post("/validate",
             tags=["Core Workflows"],
             response_model=Union[ValidationResult, ProValidationResult],
             responses={
                 400: {"model": ProblemDetails, "description": "Invalid input"},
                 500: {"model": ProblemDetails, "description": "Server error"}
             })
async def validate_facturx(
    file: UploadFile = File(..., description="Factur-X PDF or XML file to validate"),
    validate_pdfa: bool = Form(True, description="Run PDF/A-3b validation (VeraPDF). Allows bypassing for speed if PDF structure is already trusted. Requires an Evaluation or Pro key.")
):
    """
    Validate a Factur-X PDF or XML file against EN 16931 standards.
    
    Returns a validation report with detected format, flavor, and any errors.
    
    Some legacy licensed builds also return enhanced human-readable diagnostics.
    In every build, inspect validation completeness and the executed/skipped layers.
    """
    import os
    import time

    from app.license import is_licensed
    from app.metrics import metrics
    
    start_time = time.time()
    metrics.inc("requests_total")
    metrics.inc("requests_validate")
    metrics.inc_gauge("active_requests")
    
    try:
        # Read file content (async I/O - avoids blocking the event loop)
        file_content = await file.read()
        if not file_content:
            raise HTTPException(
                status_code=400,
                detail={"error": "EMPTY_FILE", "message": "File is empty"}
            )

        # Validate magic bytes: accept PDF or XML only
        filename_lower = (file.filename or "").lower()
        is_pdf_ext = filename_lower.endswith(".pdf")
        is_xml_ext = filename_lower.endswith(".xml")

        if is_pdf_ext and not _check_pdf_magic(file_content):
            raise HTTPException(
                status_code=400,
                detail={"error": "INVALID_FILE_TYPE", "message": "File does not appear to be a valid PDF (bad magic bytes)"}
            )
        if is_xml_ext and not _check_xml_magic(file_content):
            raise HTTPException(
                status_code=400,
                detail={"error": "INVALID_FILE_TYPE", "message": "File does not appear to be valid XML (bad magic bytes)"}
            )
        if not is_pdf_ext and not is_xml_ext:
            raise HTTPException(
                status_code=400,
                detail={"error": "INVALID_FILE_TYPE", "message": "Only PDF or XML files are accepted for validation"}
            )

        # LICENSE CHECK
        license_key = os.getenv("LICENSE_KEY", "").strip()
        is_pro = False
        
        from app.license import is_licensed
        if license_key:
            try:
                if is_licensed():
                    is_pro = True
                    logger.info("Licensed enhanced diagnostics enabled")
            except Exception as e:
                logger.warning(f"License check failed: {e}")
        
        # ALWAYS run Hybrid Validation (Teaser Mode for Community)
        try:
            from app.services.hybrid_validation_service import HybridValidationService
            result = HybridValidationService.validate(file_content, file.filename, validate_pdfa)
        except ImportError:
            # Fallback to basic validation if hybrid not available
            logger.warning("HybridValidationService not available, falling back to lite")
            is_valid, format_type, flavor, errors = ValidationService.validate_file(
                file_content,
                file.filename
            )
            return ValidationResult(
                valid=is_valid,
                format=format_type,
                flavor=flavor,
                errors=errors,
                validation_mode="lite"
            )
        
        # Extract all errors from hybrid result
        all_errors = result.get("errors", [])
        error_rules = [e.get("rule_id") for e in all_errors if e.get("rule_id")]
        
        # Record Metrics (Distinguish Pro vs Community for internal analytics)
        metrics.record_validation(
            mode="pro" if is_pro else "community",
            is_valid=result["is_valid"],
            profile=result.get("profile_detected"),
            error_rules=error_rules
        )
        
        if is_pro:
            # PRO MODE: Smart Diagnostics with human-readable explanations
            from app.schemas.validation import DiagnosticDetail, ProValidationResult
            from app.services.smart_diagnostics import get_diagnostics_engine
            
            engine = get_diagnostics_engine()
            # Pass XML content for proactive scan (VAT mismatch, negative totals, forbidden chars, etc.)
            xml_for_scan = result.get("xml_content")
            
            if not xml_for_scan:
                if file_content.startswith(b'<?xml') or file_content.startswith(b'<'):
                    xml_for_scan = file_content
                elif file_content.startswith(b'%PDF'):
                    try:
                        from io import BytesIO

                        from app.services.pdf_utils import get_xml_from_pdf
                        _, xml_bytes = get_xml_from_pdf(BytesIO(file_content), check_xsd=False)
                        if xml_bytes:
                            xml_for_scan = xml_bytes
                    except Exception:
                        pass
            diagnostics = engine.analyze(all_errors, xml_for_scan)
            
            diagnostic_details = [
                DiagnosticDetail(
                    rule_id=d.rule_id,
                    severity=d.severity,
                    title=d.title,
                    explanation=d.explanation,
                    suggestion=d.suggestion,
                    context=d.context if d.context else None
                )
                for d in diagnostics
            ]
            
            return ProValidationResult(
                valid=result["is_valid"],
                format=result.get("format_detected"),
                flavor=result.get("profile_detected"),
                error_count=len([d for d in diagnostics if d.severity == "error"]),
                warning_count=len([d for d in diagnostics if d.severity == "warning"]),
                diagnostics=diagnostic_details,
                validation_mode="pro_smart_diagnostics",
                pdfa_valid=result.get("pdfa_valid"),
                validation_completeness=result.get("validation_completeness", "full"),
                layers_executed=result.get("layers_executed", []),
                layers_skipped=[SkippedLayer(**s) for s in result.get("layers_skipped", [])],
            )
        else:
            # COMMUNITY MODE: Open Validation (full error list, structured format)
            from app.schemas.validation import ValidationErrorDetail
            structured_errors = []
            for e in all_errors:
                structured_errors.append(ValidationErrorDetail(
                    rule_id=e.get("rule_id"),
                    message=e.get("message", str(e)),
                    severity=e.get("severity", "error")
                ))

            return ValidationResult(
                valid=result["is_valid"],
                format=result.get("format_detected"),
                flavor=result.get("profile_detected"),
                errors=structured_errors,
                validation_mode="open_community",
                pdfa_valid=result.get("pdfa_valid"),
                validation_completeness=result.get("validation_completeness", "full"),
                layers_executed=result.get("layers_executed", []),
                layers_skipped=[SkippedLayer(**s) for s in result.get("layers_skipped", [])],
                pro_hint=None,
            )
        
    except HTTPException:
        metrics.inc("errors_total")
        raise
    except Exception as e:
        metrics.inc("errors_total")
        logger.exception(f"Unexpected error in validate endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "INTERNAL_ERROR", "message": "An unexpected error occurred"}
        )
    finally:
        metrics.dec_gauge("active_requests")
        metrics.observe("request_duration_seconds", time.time() - start_time)


@router.post("/extract",
             tags=["Core Workflows"],
             response_model=ExtractionResult,
             responses={
                 400: {"model": ProblemDetails, "description": "Invalid input"},
                 500: {"model": ProblemDetails, "description": "Server error"}
             })
async def extract_facturx(
    file: UploadFile = File(..., description="Factur-X PDF file to extract data from")
):
    """
    Inspect a Factur-X PDF and return heuristic best-effort invoice data.
    
    This endpoint is a preview/inspection workflow:
    1. Detects if the PDF contains embedded Factur-X/ZUGFeRD XML
    2. Extracts and parses the XML
    3. Returns structured invoice data (parties, totals, line items)

    The response always declares `mode=preview` and
    `suitable_for_automatic_import=false`. Values may be absent, coerced, or
    truncated by the heuristic extractor. Use `/v1/serialize` when a strict,
    versioned mapping contract is required.
    
    Use cases:
    - Human inspection and troubleshooting
    - Discovering the embedded XML and detected profile
    - Prototyping an integration before adopting a strict mapping contract
    """
    import time

    from app.metrics import metrics
    start_time = time.time()
    metrics.inc("requests_total")
    metrics.inc("requests_extract")
    metrics.inc_gauge("active_requests")
    
    try:
        # Read file content (async I/O - avoids blocking the event loop)
        file_content = await file.read()
        if not file_content:
            raise HTTPException(
                status_code=400,
                detail={"error": "EMPTY_FILE", "message": "File is empty"}
            )

        # Validate magic bytes: /extract only accepts PDF files
        if not _check_pdf_magic(file_content):
            raise HTTPException(
                status_code=400,
                detail={"error": "INVALID_FILE_TYPE", "message": "Only PDF files are accepted for extraction (bad magic bytes)"}
            )

        # Extract invoice data
        # Extraction: Always use the full ExtractionService (Open Core Policy)
        # Enhanced validation remains gated in historical licensed builds.
        from app.services.extractor import ExtractionService
        
        result = await ExtractionService.extract_invoice_data_async(
            file_content,
            file.filename
        )
        
        try:
            return ExtractionResult(**result)
        except Exception as e:
            logger.error(f"SCHEMA VALIDATION ERROR: {e}")
            raise HTTPException(status_code=500, detail=f"Schema validation failed: {str(e)}")
        
    except HTTPException:
        metrics.inc("errors_total")
        raise
    except Exception as e:
        metrics.inc("errors_total")
        logger.exception(f"Unexpected error in extract endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "INTERNAL_ERROR", "message": "An unexpected error occurred"}
        )
    finally:
        metrics.dec_gauge("active_requests")
        metrics.observe("request_duration_seconds", time.time() - start_time)

@router.post("/serialize",
             tags=["Advanced Integration"],
             response_model=SerializationResponse,
             responses={
                 400: {"model": ProblemDetails, "description": "Invalid input"},
                 422: {"model": SerializationFailureResponse, "description": "Validation or strict mapping failed"},
                 500: {"model": ProblemDetails, "description": "Server error"}
             })
async def serialize_facturx(
    file: UploadFile = File(..., description="Factur-X PDF or XML file to serialize")
):
    """
    Strict, versioned JSON serialization.

    A 200 response means that all configured validation layers passed and the
    invoice was mapped without XML recovery, invented values, or silently
    skipped material elements. The response still requires client-side supplier,
    duplicate, purchase-order, tax-policy, and payment checks.
    
    **Feature availability**: Builds without the strict serializer entitlement
    return HTTP 403. A free 30-day evaluation is linked from the project
    website; no public paid checkout is currently active.
    """
    import time

    from app.license import is_licensed
    from app.metrics import metrics
    from app.services.business_serializer import (
        BusinessReadySerializer,
        SerializationMappingError,
    )
    
    start_time = time.time()
    metrics.inc("requests_total")
    metrics.inc("requests_serialize")
    metrics.inc_gauge("active_requests")
    
    try:
        # Read file content (async I/O - avoids blocking the event loop)
        file_content = await file.read()
        if not file_content:
            raise HTTPException(
                status_code=400,
                detail={"error": "EMPTY_FILE", "message": "File is empty"}
            )

        # Validate magic bytes before licence check (no point wasting CPU on garbage)
        filename_lower = (file.filename or "").lower()
        if filename_lower.endswith(".pdf") and not _check_pdf_magic(file_content):
            raise HTTPException(
                status_code=400,
                detail={"error": "INVALID_FILE_TYPE", "message": "File does not appear to be a valid PDF (bad magic bytes)"}
            )
        if filename_lower.endswith(".xml") and not _check_xml_magic(file_content):
            raise HTTPException(
                status_code=400,
                detail={"error": "INVALID_FILE_TYPE", "message": "File does not appear to be valid XML (bad magic bytes)"}
            )

        from app.license import has_tier, is_licensed
        
        try:
            if is_licensed():
                logger.info("Licensed strict serialization enabled")
        except Exception:
            pass

        is_pro_tier = has_tier(["Evaluation", "Pro"])
        if not is_pro_tier:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "FEATURE_NOT_ENABLED",
                    "message": "Factur-X Engine Intake requires an Evaluation or Pro key. A free 30-day evaluation is linked from the project website; no public paid checkout is active."
                }
            )

        # Extract XML if it's a PDF
        xml_data = None
        if file.filename.lower().endswith('.pdf'):
            from app.services.pdf_utils import get_xml_from_pdf
            try:
                # get_xml_from_pdf returns (filename, xml_content)
                _, xml_data = get_xml_from_pdf(file_content)
            except Exception as e:
                logger.error(f"XML Extraction failed: {e}")
        else:
            xml_data = file_content

        if not xml_data:
            raise HTTPException(
                status_code=400,
                detail={"error": "NO_XML_FOUND", "message": "No Factur-X/ZUGFeRD XML found in file"}
            )
            
        # Ensure xml_data is bytes (avoid list error if extraction returns something else)
        if isinstance(xml_data, list) and len(xml_data) > 0:
            xml_data = xml_data[0]
        if not isinstance(xml_data, (bytes, str)):
            xml_data = str(xml_data).encode('utf-8')
        elif isinstance(xml_data, str):
            xml_data = xml_data.encode('utf-8')

        # Validate the structured invoice before mapping. PDF/A is deliberately
        # outside this endpoint's success contract: /serialize normalizes invoice
        # data and does not certify the PDF container.
        from app.services.hybrid_validation_service import HybridValidationService

        validation_result = HybridValidationService.validate(
            xml_data,
            "invoice.xml",
            validate_pdfa=False,
        )
        validation_completeness = validation_result.get("validation_completeness", "partial")
        if validation_completeness != "full":
            skipped = validation_result.get("layers_skipped", [])
            diagnostics = [
                SerializationDiagnostic(
                    code="VALIDATION_LAYER_SKIPPED",
                    message=f"Validation layer '{item.get('layer', 'unknown')}' did not run: {item.get('reason', 'unknown reason')}",
                    source="validation",
                    path=item.get("layer"),
                )
                for item in skipped
            ]
            if not diagnostics:
                diagnostics = [
                    SerializationDiagnostic(
                        code="VALIDATION_INCOMPLETE",
                        message="The configured validation pipeline did not report a complete result.",
                        source="validation",
                    )
                ]
            failure = SerializationFailureResponse(
                engine_version=__version__,
                execution_status="complete",
                mapping_status="not_started",
                validation_status="incomplete",
                suggested_route="manual_review",
                errors=diagnostics,
            )
            return JSONResponse(status_code=422, content=failure.model_dump(mode="json"))

        if not validation_result.get("is_valid", False):
            diagnostics = [
                SerializationDiagnostic(
                    code=error.get("rule_id") or "VALIDATION_REJECTED",
                    message=error.get("message") or "The invoice failed validation.",
                    source="validation",
                    path=error.get("location"),
                    severity="warning" if error.get("severity") == "warning" else "error",
                )
                for error in validation_result.get("errors", [])
            ]
            if not diagnostics:
                diagnostics = [
                    SerializationDiagnostic(
                        code="VALIDATION_REJECTED",
                        message="The invoice failed validation.",
                        source="validation",
                    )
                ]
            failure = SerializationFailureResponse(
                engine_version=__version__,
                execution_status="complete",
                mapping_status="not_started",
                validation_status="rejected",
                suggested_route="reject_input",
                errors=diagnostics,
            )
            return JSONResponse(status_code=422, content=failure.model_dump(mode="json"))

        # Strict mapping
        try:
            invoice_data = BusinessReadySerializer.serialize(xml_data, is_pro=is_pro_tier)
            
            return SerializationResponse(
                engine_version=__version__,
                invoice=invoice_data,
            )
        except SerializationMappingError as exc:
            failure = SerializationFailureResponse(
                engine_version=__version__,
                execution_status="complete",
                mapping_status="failed",
                validation_status="passed",
                suggested_route="manual_review",
                errors=exc.diagnostics,
            )
            return JSONResponse(status_code=422, content=failure.model_dump(mode="json"))
        
    except HTTPException:
        metrics.inc("errors_total")
        raise
    except Exception as e:
        metrics.inc("errors_total")
        logger.exception(f"Unexpected error in serialize endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "INTERNAL_ERROR", "message": "An unexpected error occurred"}
        )
    finally:
        metrics.dec_gauge("active_requests")
        metrics.observe("request_duration_seconds", time.time() - start_time)


@router.post("/merge",
             tags=["Core Workflows"],
             response_class=StreamingResponse,
             responses={
                 200: {"description": "Factur-X PDF with embedded XML (final PDF/A status not asserted)"},
                 400: {"model": ProblemDetails, "description": "Invalid file type"},
                 409: {"model": ProblemDetails, "description": "PDF already contains Factur-X XML"},
                 422: {"model": ProblemDetails, "description": "Input not PDF/A-3b or invalid XML"},
                 500: {"model": ProblemDetails, "description": "Server error"},
             })
async def merge_facturx(
    pdf: UploadFile = File(..., description="PDF/A-3b input (without embedded XML)"),
    xml: UploadFile = File(..., description="Factur-X/ZUGFeRD/XRechnung XML to embed"),
    format: Optional[str] = Form(None, description="Optional format override: factur-x, zugferd, or xrechnung"),
):
    """
    Embed an existing XML (Factur-X/ZUGFeRD/XRechnung) into a PDF container.

    **Community endpoint** - no license required.

    This endpoint validates input constraints, but does not prove final PDF/A compliance of the produced file.
    Use /v1/validate on the output when PDF/A evidence is required.

    Errors:
    - **400** Bad file (not PDF or not XML)
    - **409** PDF already contains embedded Factur-X XML
    - **422** Input PDF is not declared PDF/A-3b, or XML fails EN 16931 validation
    """
    import time

    from app.metrics import metrics
    start_time = time.time()
    metrics.inc("requests_total")
    metrics.inc("requests_merge")
    metrics.inc_gauge("active_requests")

    try:
        pdf_content = await pdf.read()
        xml_content = await xml.read()

        # Validate magic bytes
        if not _check_pdf_magic(pdf_content):
            raise HTTPException(
                status_code=400,
                detail={"error": "INVALID_FILE_TYPE", "message": "First upload must be a valid PDF file"}
            )
        if not _check_xml_magic(xml_content):
            raise HTTPException(
                status_code=400,
                detail={"error": "INVALID_FILE_TYPE", "message": "Second upload must be a valid XML file"}
            )

        # 409 - PDF already has embedded Factur-X XML
        _, existing_xml = get_xml_from_pdf(BytesIO(pdf_content), check_xsd=False)
        if existing_xml is not None:
            raise HTTPException(
                status_code=409,
                detail={
                    "error": "ALREADY_FACTURX",
                    "message": "This PDF already contains embedded Factur-X XML. Use /validate to inspect it.",
                }
            )

        # 422 - PDF is not PDF/A-3b (XMP metadata check)
        if not is_pdfa3b(pdf_content):
            raise HTTPException(
                status_code=422,
                detail={
                    "error": "NOT_PDFA3",
                    "message": "Input PDF is not PDF/A-3b compliant. Only PDF/A-3b PDFs are supported for merge.",
                }
            )

        # Merge: validate XML + embed
        try:
            result_pdf, detected_format, detected_profile = GeneratorService.merge_xml_to_pdf(
                pdf_content, xml_content, force_format=format
            )
        except ValueError as e:
            raise HTTPException(
                status_code=422,
                detail={"error": "MERGE_FAILED", "message": str(e)}
            )

        return StreamingResponse(
            BytesIO(result_pdf),
            media_type="application/pdf",
            headers={
                "Content-Disposition": 'attachment; filename="facturx_merged.pdf"',
                "X-Facturx-Format": detected_format,
                "X-Facturx-Profile": detected_profile,
            },
        )

    except HTTPException:
        metrics.inc("errors_total")
        raise
    except Exception as e:
        metrics.inc("errors_total")
        logger.exception(f"Unexpected error in merge endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "INTERNAL_ERROR", "message": "An unexpected error occurred"}
        )
    finally:
        metrics.dec_gauge("active_requests")
        metrics.observe("request_duration_seconds", time.time() - start_time)
