"""
Factur-X PDF generation service using Jinja2 templating and factur-x library.
"""
import logging
from io import BytesIO
from pathlib import Path
from jinja2 import FileSystemLoader, select_autoescape
from jinja2.sandbox import SandboxedEnvironment # SECURITY: Prevents SSTI/RCE
from facturx import generate_from_binary
from app.schemas.validation import InvoiceMetadata

logger = logging.getLogger(__name__)

# Load Jinja2 environment (Sandboxed)
TEMPLATE_DIR = Path(__file__).parent.parent / "templates"
jinja_env = SandboxedEnvironment(
    loader=FileSystemLoader(TEMPLATE_DIR),
    autoescape=select_autoescape(['xml']),
    trim_blocks=True,
    lstrip_blocks=True
)


class GeneratorService:
    """Service for generating Factur-X PDFs."""

    @staticmethod
    def generate_xml(metadata: InvoiceMetadata) -> str:
        """
        Generate Factur-X XML from metadata using Jinja2 template.
        
        Args:
            metadata: Invoice metadata.
            
        Returns:
            XML string.
        """
        try:
            template = jinja_env.get_template("factur-x.xml.j2")
            
            # Prepare context for template
            context = {
                "invoice_number": metadata.invoice_number,
                "issue_date": metadata.issue_date,
                "seller": metadata.seller.model_dump(),
                "buyer": metadata.buyer.model_dump(),
                "lines": [l.model_dump() for l in metadata.lines],
                "tax_details": [t.model_dump() for t in metadata.tax_details],
                "amounts": metadata.amounts.model_dump(),
                "currency_code": metadata.currency_code,
                "profile": metadata.profile,
                "document_type_code": metadata.document_type_code,
            }
            
            xml_content = template.render(**context)
            logger.info(f"Generated XML for invoice {metadata.invoice_number}")
            return xml_content
            
        except Exception as e:
            logger.error(f"Failed to generate XML: {e}")
            raise ValueError(f"XML generation failed: {str(e)}")

    @staticmethod
    def generate_facturx_pdf(pdf_content: bytes, metadata: InvoiceMetadata) -> bytes:
        """
        Generate Factur-X PDF by embedding XML into a regular PDF.
        
        Args:
            pdf_content: Original PDF bytes.
            metadata: Invoice metadata.
            
        Returns:
            Factur-X PDF bytes.
        """
        try:
            # Generate XML from metadata
            xml_content = GeneratorService.generate_xml(metadata)
            
            # Convert to bytes
            xml_bytes = xml_content.encode('utf-8')
            
            # Use factur-x library to generate Factur-X PDF
            logger.info("Generating Factur-X PDF...")
            result_bytes = generate_from_binary(
                pdf_content,  # First positional arg: input PDF bytes
                xml_bytes,    # Second positional arg: XML bytes
                flavor='factur-x',
                level=metadata.profile,
                pdf_metadata={
                    'author': 'Factur-X API',
                    'keywords': 'Factur-X, ZUGFeRD, e-invoice',
                    'title': f'Invoice {metadata.invoice_number}',
                    'subject': 'Factur-X Invoice',
                }
            )
            
            logger.info(f"Successfully generated Factur-X PDF for invoice {metadata.invoice_number}")
            
            # AUTOMATIC VALIDATION (Quality Gate)
            # Ensure we never deliver a broken or non-compliant file
            from app.services.validator import ValidationService
            is_valid, _, _, errors = ValidationService.validate_file(result_bytes, "generated_check.pdf")
            
            if not is_valid:
                logger.error(f"Generated PDF failed validation: {errors}")
                # We fail strict. A generated invoice MUST be valid.
                raise ValueError(f"Generated Factur-X PDF failed compliance check: {errors[0]}")
                
            return result_bytes
            
        except Exception as e:
            logger.error(f"Failed to generate Factur-X PDF: {e}")
            raise ValueError(f"Factur-X PDF generation failed: {str(e)}")
