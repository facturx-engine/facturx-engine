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
async def convert_to_facturx(
    pdf: UploadFile = File(..., description="Original PDF invoice"),
    metadata: str = Form(..., description="Invoice metadata as JSON")
):
    """
    Convert a standard PDF invoice + JSON metadata into a Factur-X PDF.
    
    The output PDF is PDF/A-3 compliant with embedded XML.
    """
    try:
        # Validate file type
        if not pdf.filename.lower().endswith('.pdf'):
            raise HTTPException(
                status_code=400,
                detail={"error": "INVALID_FILE_TYPE", "message": "Only PDF files are accepted"}
            )
        
        # Read PDF content
        pdf_content = await pdf.read()
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
        raise
    except Exception as e:
        logger.exception(f"Unexpected error in convert endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "INTERNAL_ERROR", "message": "An unexpected error occurred"}
        )


@router.post("/validate",
             response_model=ValidationResult,
             responses={
                 400: {"model": ErrorResponse, "description": "Invalid input"},
                 500: {"model": ErrorResponse, "description": "Server error"}
             })
async def validate_facturx(
    file: UploadFile = File(..., description="Factur-X PDF or XML file to validate")
):
    """
    Validate a Factur-X PDF or XML file against EN 16931 standards.
    
    Returns a validation report with detected format, flavor, and any errors.
    """
    try:
        # Read file content
        file_content = await file.read()
        if not file_content:
            raise HTTPException(
                status_code=400,
                detail={"error": "EMPTY_FILE", "message": "File is empty"}
            )
        
        # Validate file
        is_valid, format_type, flavor, errors = ValidationService.validate_file(
            file_content,
            file.filename
        )
        
        return ValidationResult(
            valid=is_valid,
            format=format_type,
            flavor=flavor,
            errors=errors
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error in validate endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "INTERNAL_ERROR", "message": "An unexpected error occurred"}
        )


@router.post("/extract",
             response_model=ExtractionResult,
             responses={
                 400: {"model": ErrorResponse, "description": "Invalid input"},
                 500: {"model": ErrorResponse, "description": "Server error"}
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
    try:
        # Read file content
        file_content = await file.read()
        if not file_content:
            raise HTTPException(
                status_code=400,
                detail={"error": "EMPTY_FILE", "message": "File is empty"}
            )
        
        # Extract invoice data
        # LICENSE CHECK: Dynamically load Pro or Demo extractor
        import os
        from app.license import is_licensed
        
        license_key = os.getenv("LICENSE_KEY", "").strip()
        use_pro = False
        
        if license_key:
             try:
                 if is_licensed():
                     use_pro = True
             except:
                 pass
        
        if use_pro:
            # Pro Mode: Import from optimized/compiled module
            try:
                from app.services.extractor import ExtractionService
                logger.info("Extracting with PRO Engine")
            except ImportError:
                # Fallback if pro module missing (should not happen in pro build)
                from app.services.extractor_demo import ExtractionService
                logger.warning("Pro Engine missing, falling back to Demo")
        else:
            # Demo Mode: Import from community stub
            from app.services.extractor_demo import ExtractionService
            logger.info("Extracting with DEMO Engine")

        result = ExtractionService.extract_invoice_data(
            file_content,
            file.filename
        )
        
        return ExtractionResult(**result)
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"Unexpected error in extract endpoint: {e}")
        raise HTTPException(
            status_code=500,
            detail={"error": "INTERNAL_ERROR", "message": "An unexpected error occurred"}
        )
