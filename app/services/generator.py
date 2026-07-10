"""
Factur-X PDF generation service using Jinja2 templating and factur-x library.
"""
import logging
from pathlib import Path
from typing import Optional, Tuple

from facturx import generate_from_binary
from jinja2 import FileSystemLoader, select_autoescape
from jinja2.sandbox import SandboxedEnvironment  # SECURITY: Prevents SSTI/RCE

from app.schemas.validation import InvoiceMetadata

logger = logging.getLogger(__name__)

# Load Jinja2 environment (Sandboxed)
TEMPLATE_DIR = Path(__file__).parent.parent / "templates"
jinja_env = SandboxedEnvironment(
    loader=FileSystemLoader(TEMPLATE_DIR),
    autoescape=select_autoescape(['xml', 'xml.j2']),
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
            # Prepare context for template
            # Use model_dump to automatically include all new fields (IBAN, ShipTo, etc.)
            # exclude_none=True ensures Jinja2 'default' filters work correctly for missing optional fields
            context = metadata.model_dump(exclude_none=True)
            
            xml_content = template.render(**context)
            logger.debug(f"Generated XML content:\n{xml_content}")
            logger.info(f"Generated XML for invoice {metadata.invoice_number}")
            return xml_content
            
        except Exception as e:
            logger.error(f"Failed to generate XML: {e}")
            raise ValueError(f"XML generation failed: {str(e)}")

    @staticmethod
    def attach_xml_to_pdf(pdf_content: bytes, metadata: InvoiceMetadata) -> bytes:
        """
        Takes an existing PDF and attaches the Factur-X XML.
        
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
            # Mapping for factur-x library (which might not know about 'xrechnung_3.0' profile name yet)
            lib_level = metadata.profile
            if lib_level == "xrechnung_3.0":
                lib_level = "en16931" # Use en16931 base for library embedding, template handles the ID
                
            result_bytes = generate_from_binary(
                pdf_content,  # First positional arg: input PDF bytes
                xml_bytes,    # Second positional arg: XML bytes
                flavor='factur-x',
                level=lib_level,
                check_xsd=False,         # Engine validates XSD via Saxon
                pdf_metadata={
                    'author': 'Factur-X API',
                    'keywords': 'Factur-X, ZUGFeRD, e-invoice',
                    'title': f'Invoice {metadata.invoice_number}',
                    'subject': f'Factur-X Invoice ({metadata.profile})',
                }
            )
            
            logger.info(f"Successfully generated Factur-X PDF for invoice {metadata.invoice_number}")
            
            # AUTOMATIC VALIDATION (Quality Gate)
            # Ensure we never deliver a broken or non-compliant file
            from app.services.hybrid_validation_service import HybridValidationService
            # OPTIMIZATION: Validate raw XML bytes directly to avoid expensive PDF extraction
            validation_res = HybridValidationService.validate(xml_bytes, "generated_check.xml")
            
            if not validation_res["is_valid"]:
                errors = validation_res.get("errors", [])
                error_msg = errors[0].get("message") if errors else "Unknown validation error"
                logger.error(f"Generated PDF failed compliance check: {errors}")
                # We fail strict. A generated invoice MUST be valid.
                raise ValueError(f"Generated Factur-X PDF failed compliance check: {error_msg}")
                
            return result_bytes
            
        except Exception as e:
            logger.error(f"Failed to generate Factur-X PDF: {e}")
            raise ValueError(f"Factur-X PDF generation failed: {str(e)}")

    @staticmethod
    def merge_xml_to_pdf(
        pdf_content: bytes,
        xml_content: bytes,
        force_format: Optional[str] = None,
    ) -> Tuple[bytes, str, str]:
        """
        Embed an existing XML into a PDF/A-3b to produce a Factur-X PDF.

        Args:
            pdf_content: Original PDF/A-3b bytes.
            xml_content: Valid Factur-X/ZUGFeRD/XRechnung XML bytes.
            force_format: Optional override for format detection (e.g. "factur-x").

        Returns:
            Tuple of (pdf_bytes, detected_format, detected_profile).

        Raises:
            ValueError: If XML parsing or validation fails.
        """
        from lxml import etree

        from app.services.hybrid_validation_service import HybridValidationService
        from app.services.validation_utils import detect_format

        # 1. Parse XML securely and detect format
        secure_parser = etree.XMLParser(resolve_entities=False, no_network=True, recover=False)
        try:
            xml_tree = etree.fromstring(xml_content, parser=secure_parser)
        except etree.XMLSyntaxError as e:
            raise ValueError(f"XML parsing failed: {e}")

        if force_format:
            parts = force_format.split(":", 1)
            fmt: Optional[str] = parts[0] or None
            profile: Optional[str] = parts[1] if len(parts) > 1 else "en16931"
        else:
            try:
                fmt, profile = detect_format(xml_tree)
            except Exception as e:
                raise ValueError(f"Unable to detect XML format: {e}")

        # 2. Validate XML (Community scope: XSD + Schematron, no VeraPDF)
        validation = HybridValidationService.validate(
            xml_content, "merge_input.xml", validate_pdfa=False
        )
        if not validation["is_valid"]:
            errors = [e["message"] for e in validation.get("errors", [])]
            raise ValueError(f"XML validation failed: {'; '.join(errors[:3])}")

        # 3. Map profile for xrechnung_3.0 (same convention as attach_xml_to_pdf)
        lib_level = "en16931" if profile == "xrechnung_3.0" else (profile or "en16931")

        # UBL format: embed as factur-x container (library does not handle ubl flavor directly)
        lib_flavor = "factur-x" if fmt == "ubl" else (fmt or "factur-x")

        # 4. Embed XML — library sets AFRelationship=/Data internally
        logger.info(f"Merging XML into PDF: flavor={lib_flavor}, level={lib_level}")
        result_bytes = generate_from_binary(
            pdf_content,
            xml_content,
            flavor=lib_flavor,
            level=lib_level,
            check_xsd=False,         # Engine validates XSD via Saxon
        )

        return result_bytes, fmt or "factur-x", profile or "en16931"
