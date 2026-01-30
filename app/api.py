"""
FastAPI route handlers for Factur-X API.
"""
import logging
import json
from fastapi import APIRouter, UploadFile, File, Form, HTTPException
from fastapi.responses import StreamingResponse
from io import BytesIO

from app.schemas.validation import InvoiceMetadata, ValidationResult, ErrorResponse
from app.schemas.extraction import ExtractionResult
from app.services.generator import GeneratorService
from app.services.validator import ValidationService

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/v1", tags=["factur-x"])


@router.post("/convert", 
             response_class=StreamingResponse,
             responses={
                 200: {"description": "Factur-X PDF successfully generated"},
                 400: {"model": ErrorResponse, "description": "Invalid input"},
                 500: {"model": ErrorResponse, "description": "Server error"}
             })
def convert_to_facturx(
    pdf: UploadFile = File(..., description="Original PDF invoice"),
    metadata: str = Form(..., description="Invoice metadata as JSON")
):
    """
    Convert a standard PDF invoice + JSON metadata into a Factur-X PDF.
    
    The output PDF is PDF/A-3 compliant with embedded XML.
    """
    import time
    from app.metrics import metrics
    start_time = time.time()
    metrics.inc("requests_total")
    metrics.inc("requests_convert")
    metrics.inc_gauge("active_requests")
    
    try:
        # Validate file type
        if not pdf.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail={"error": "INVALID_FILE_TYPE", "message": "Only PDF files are accepted"}
            )
        
        # Read PDF content (Sync read for sync route)
        pdf_content = pdf.file.read()
        if not pdf_content:
            raise HTTPException(
                status_code=400,
                detail={"error": "EMPTY_FILE", "message": "PDF file is empty"}
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
            facturx_pdf = GeneratorService.generate_facturx_pdf(pdf_content, invoice_metadata)
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
                 400: {"model": ErrorResponse, "description": "Invalid input"},
                 500: {"model": ErrorResponse, "description": "Server error"}
             })
def generate_facturx_xml(
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
        metrics.observe("request_duration_seconds", time.time() - start_time)


@router.post("/validate",
             response_model=ValidationResult,
             responses={
                 400: {"model": ErrorResponse, "description": "Invalid input"},
                 500: {"model": ErrorResponse, "description": "Server error"}
             })
def validate_facturx(
    file: UploadFile = File(..., description="Factur-X PDF or XML file to validate")
):
    """
    Validate a Factur-X PDF or XML file against EN 16931 standards.
    
    Returns a validation report with detected format, flavor, and any errors.
    
    **Pro Edition**: Full compliance report with all errors detailed.
    **Community Edition (Teaser)**: Shows first error + count of hidden errors.
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
        # Read file content (Sync read)
        file_content = file.file.read()
        if not file_content:
            raise HTTPException(
                status_code=400,
                detail={"error": "EMPTY_FILE", "message": "File is empty"}
            )
        
        # LICENSE CHECK
        license_key = os.getenv("LICENSE_KEY", "").strip()
        is_pro = False
        
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
            result = HybridValidationService.validate(file_content, file.filename)
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
        total_error_count = len(all_errors)
        
        if is_pro:
            # PRO MODE: Full compliance report
            error_messages = [e.get("message", str(e)) for e in all_errors]
            error_rules = [e.get("rule_id") for e in all_errors if e.get("rule_id")]
            
            # PRO-TIER METRICS
            metrics.record_validation(
                mode="pro",
                is_valid=result["is_valid"],
                profile=result.get("profile_detected"),
                error_rules=error_rules
            )
            
            return ValidationResult(
                valid=result["is_valid"],
                format=result.get("format_detected"),
                flavor=result.get("profile_detected"),
                errors=error_messages,
                validation_mode="pro"
            )
        else:
            # TEASER MODE: Show first error + hidden count
            if total_error_count == 0:
                # No errors - valid file
                metrics.record_validation(
                    mode="teaser",
                    is_valid=True,
                    profile=result.get("profile_detected")
                )
                return ValidationResult(
                    valid=True,
                    format=result.get("format_detected"),
                    flavor=result.get("profile_detected"),
                    errors=[],
                    validation_mode="teaser"
                )
            else:
                # Show ONLY first error + teaser message
                first_error = all_errors[0]
                hidden_count = total_error_count - 1
                
                teaser_errors = [
                    f"[{first_error.get('rule_id', 'RULE')}] {first_error.get('message', 'Erreur de conformité détectée')}"
                ]
                
                if hidden_count > 0:
                    teaser_errors.append(
                        f"⚠️ {hidden_count} autres erreurs de conformité critique détectées. "
                        f"Activez la version Pro pour le rapport complet et garantir l'acceptation par Chorus Pro/PPF."
                    )
                
                # TEASER CONVERSION METRICS
                error_rules = [e.get("rule_id") for e in all_errors if e.get("rule_id")]
                metrics.record_validation(
                    mode="teaser",
                    is_valid=False,
                    profile=result.get("profile_detected"),
                    error_rules=error_rules,
                    hidden_count=hidden_count
                )
                
                return ValidationResult(
                    valid=False,
                    format=result.get("format_detected"),
                    flavor=result.get("profile_detected"),
                    errors=teaser_errors,
                    validation_mode="teaser"
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
                 400: {"model": ErrorResponse, "description": "Invalid input"},
                 500: {"model": ErrorResponse, "description": "Server error"}
             })
def extract_facturx(
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
        # Read file content (Sync read)
        file_content = file.file.read()
        if not file_content:
            raise HTTPException(
                status_code=400,
                detail={"error": "EMPTY_FILE", "message": "File is empty"}
            )
        
        # Extract invoice data
        # Extraction: Always use the full ExtractionService (Open Core Policy)
        # Pro features are now strictly on Validation and Metrics.
        from app.services.extractor import ExtractionService
        
        result = ExtractionService.extract_invoice_data(
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

