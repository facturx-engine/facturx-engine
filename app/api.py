"""
FastAPI route handlers for Factur-X API.
"""
import logging
import json
from typing import Union
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from io import BytesIO

# Magic-byte signatures for supported file types
_PDF_MAGIC = b"%PDF-"
_XML_MAGIC_BYTES = (b"<?xml", b"\xef\xbb\xbf<?xml", b"<rsm:", b"<ubl:")  # UTF-8 BOM + common root elements

def _check_pdf_magic(content: bytes) -> bool:
    """Return True if content starts with the PDF magic bytes (%PDF-)."""
    return content[:5] == _PDF_MAGIC

def _check_xml_magic(content: bytes) -> bool:
    """Return True if content looks like XML (starts with <?xml or a known root element)."""
    stripped = content.lstrip(b"\xef\xbb\xbf \t\r\n")  # strip UTF-8 BOM + whitespace
    return stripped[:5] == b"<?xml" or stripped[:4] in (b"<rsm", b"<ubl", b"<Cro")

from app.schemas.validation import InvoiceMetadata, ValidationResult, ProValidationResult
from app.schemas.errors import ProblemDetails
from app.schemas.extraction import ExtractionResult
from app.schemas.integration import SerializationResponse
from app.services.generator import GeneratorService
from app.services.validator import ValidationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["factur-x"])


@router.post("/convert", 
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
    
    The input must be a valid PDF file (Max 20MB). The API will generate the XML 
    from the metadata and embed it into the PDF to create a PDF/A-3 compliant Factur-X invoice.
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

        # Read PDF content (async I/O — avoids blocking the event loop)
        pdf_content = await pdf.read()
        if not pdf_content:
            raise HTTPException(
                status_code=400,
                detail={"error": "EMPTY_FILE", "message": "PDF file is empty"}
            )

        # Validate magic bytes (second pass — catches renamed non-PDF files)
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
                "Content-Disposition": f"attachment; filename=facturx_{invoice_metadata.invoice_number}.pdf"
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
                "Content-Disposition": f"attachment; filename=facturx_{invoice_metadata.invoice_number}.xml"
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
             response_model=Union[ValidationResult, ProValidationResult],
             responses={
                 400: {"model": ProblemDetails, "description": "Invalid input"},
                 500: {"model": ProblemDetails, "description": "Server error"}
             })
async def validate_facturx(
    file: UploadFile = File(..., description="Factur-X PDF or XML file to validate"),
    validate_pdfa: bool = Form(True, description="Run PDF/A-3b validation (VeraPDF). Allows bypassing for speed if PDF structure is already trusted. Pro only.")
):
    """
    Validate a Factur-X PDF or XML file against EN 16931 standards.
    
    Returns a validation report with detected format, flavor, and any errors.
    
    **Pro Edition**: Smart Diagnostics with actionable human-readable fixes.
    **Community Edition**: Full raw validation report (Standard EN16931 error codes).
    """
    import time
    import os
    from app.metrics import metrics
    from app.license import is_licensed
    
    start_time = time.time()
    metrics.inc("requests_total")
    metrics.inc("requests_validate")
    metrics.inc_gauge("active_requests")
    
    try:
        # Read file content (async I/O — avoids blocking the event loop)
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
                    logger.info("PRO License validated - Full compliance report enabled")
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
            from app.services.smart_diagnostics import get_diagnostics_engine
            from app.schemas.validation import ProValidationResult, DiagnosticDetail
            
            engine = get_diagnostics_engine()
            diagnostics = engine.analyze(all_errors)
            
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
             response_model=ExtractionResult,
             responses={
                 400: {"model": ProblemDetails, "description": "Invalid input"},
                 500: {"model": ProblemDetails, "description": "Server error"}
             })
async def extract_facturx(
    file: UploadFile = File(..., description="Factur-X PDF file to extract data from")
):
    """
    Extract Factur-X XML from a PDF and return structured invoice data as JSON.
    
    This endpoint is designed for invoice reception workflows:
    1. Detects if the PDF contains embedded Factur-X/ZUGFeRD XML
    2. Extracts and parses the XML
    3. Returns structured invoice data (parties, totals, line items)
    
    Use cases:
    - Automated invoice reception
    - ERP integration
    - Invoice validation before processing
    """
    import time
    from app.metrics import metrics
    start_time = time.time()
    metrics.inc("requests_total")
    metrics.inc("requests_extract")
    metrics.inc_gauge("active_requests")
    
    try:
        # Read file content (async I/O — avoids blocking the event loop)
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
        # Pro features are now strictly on Validation and Metrics.
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
             response_model=SerializationResponse,
             responses={
                 400: {"model": ProblemDetails, "description": "Invalid input"},
                 500: {"model": ProblemDetails, "description": "Server error"}
             })
async def serialize_facturx(
    file: UploadFile = File(..., description="Factur-X PDF or XML file to serialize")
):
    """
    Business-Ready JSON Serialization (Pro Feature).
    
    Transforms XML data into a normalized, high-precision JSON format 
    designed for ERP and accounting system integration.
    
    **Trial Mode**: Available for reference files.
    **Community Mode**: Returns obfuscated (masked) data for schema testing.
    """
    import time
    from app.metrics import metrics
    from app.license import is_licensed
    from app.services.business_serializer import BusinessReadySerializer
    
    start_time = time.time()
    metrics.inc("requests_total")
    metrics.inc("requests_serialize")
    metrics.inc_gauge("active_requests")
    
    try:
        # Read file content (async I/O — avoids blocking the event loop)
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
                logger.info("PRO License validated for /serialize")
        except Exception:
            pass

        is_pro_tier = has_tier(["Evaluation", "Business", "Enterprise"])
        if not is_pro_tier:
            raise HTTPException(
                status_code=403,
                detail={
                    "error": "LICENSE_REQUIRED", 
                    "message": "The Business-Ready Serialization is a Pro feature. Get your free 30-day evaluation key at https://facturx-engine.lemonsqueezy.com"
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

        # Serialize
        try:
            invoice_data = BusinessReadySerializer.serialize(
                xml_data, 
                is_pro=is_pro_tier
            )
            
            return SerializationResponse(
                success=True,
                invoice=invoice_data
            )
        except Exception as e:
            logger.exception(f"Serialization failed: {e}")
            return SerializationResponse(
                success=False,
                errors=[{"error": "SERIALIZATION_FAILED", "message": str(e)}]
            )
        
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
