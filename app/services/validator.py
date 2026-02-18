import logging
from io import BytesIO
from pathlib import Path
from typing import Tuple, Optional, List
from facturx import xml_check_xsd, get_level, get_flavor
from app.services.pdf_utils import get_xml_from_pdf
from lxml import etree

logger = logging.getLogger(__name__)


from app.services.validation_utils import humanize_errors, detect_format

class ValidationService:
    """Service for validating Factur-X/ZUGFeRD files."""

    # Security: Configure strict XML parser to prevent XXE and DoS attacks
    _SECURE_PARSER = etree.XMLParser(
        resolve_entities=False,  # Block XXE
        no_network=True,         # Block network access
        huge_tree=False,         # Block DoS attacks
        recover=False            # Strict validation
    )

    # Assets Path
    _SCHEMATRON_DIR = Path(__file__).parent.parent / "assets" / "schematron"
    
    # Pre-compiled XSLT validator (Singleton)
    _CORE_VALIDATOR: Optional[etree.XSLT] = None

    @classmethod
    def _initialize_schematrons(cls):
        """Initializes XSLT validators if not already loaded."""
        if cls._CORE_VALIDATOR is None:
            # We use a combined file for core EN16931 + FR business rules 
            # optimized for Python (XPath 1.0)
            core_path = cls._SCHEMATRON_DIR / "facturx_py_rules.xsl"
            if core_path.exists():
                try:
                    cls._CORE_VALIDATOR = etree.XSLT(etree.parse(str(core_path)))
                    logger.info("Loaded Factur-X Python-Compatible Business Rules (XSLT)")
                except Exception as e:
                    logger.error(f"Failed to load Core Rules: {e}")

    @staticmethod
    def _check_schematron(xml_etree: etree._Element, validator: etree.XSLT) -> List[str]:
        """Runs Schematron validation and extracts failed assertions."""
        errors = []
        try:
            # SVRL (Schematron Validation Report Language) output
            result_tree = validator(xml_etree)
            if result_tree is None:
                return []

            # Find all failed assertions in the SVRL report
            ns = {"svrl": "http://purl.oclc.org/dsdl/svrl"}
            failed_asserts = result_tree.xpath("//svrl:failed-assert", namespaces=ns)
            
            for assertion in failed_asserts:
                # Check severity
                severity = assertion.get("severity", "fatal").lower()
                is_blocking = severity not in ["warning", "info"]
                
                text_elem = assertion.xpath("svrl:text", namespaces=ns)
                msg_text = text_elem[0].text if (text_elem and text_elem[0].text) else "Unknown rule violation"
                
                # Format: "[WARNING] Message" vs "Message"
                final_msg = msg_text.strip()
                if not is_blocking:
                    logger.warning(f"Schematron Warning: {final_msg}")
                    # We do NOT add to 'errors' list if we want is_valid=True for warnings
                    # OR we add it but need a way to distinguish.
                    # Current contract: is_valid=False if errors is not empty.
                    continue 

                errors.append(final_msg)
                
                if not msg_text:
                     errors.append(assertion.get("id", "Unknown ID"))
        except Exception as e:
            logger.error(f"Schematron execution failed: {type(e).__name__}: {e}")
            # We don't block the invoice if the validator itself crashes
        return errors

    @staticmethod
    def validate_file(file_content: bytes, filename: str) -> Tuple[bool, Optional[str], Optional[str], List[str]]:
        """
        Validate a Factur-X PDF or XML file.
        
        Args:
            file_content: Raw file bytes.
            filename: Original filename (used for type detection).
            
        Returns:
            Tuple of (is_valid, format, flavor, errors_list).
        """
        # Ensure validators are loaded
        ValidationService._initialize_schematrons()
        
        detected_format = None
        detected_flavor = None
        
        try:
            # Detect file type
            is_pdf = filename.lower().endswith('.pdf') or file_content.startswith(b'%PDF')
            
            if is_pdf:
                # Extract XML from PDF
                logger.debug(f"Validating PDF file: {filename}")
                try:
                    xml_filename, xml_content = get_xml_from_pdf(
                        BytesIO(file_content),
                        check_xsd=False
                    )
                    if not xml_content:
                        return False, None, None, ["No Factur-X/ZUGFeRD XML found in PDF"]
                except Exception as e:
                    return False, None, None, [f"Failed to extract XML from PDF: {str(e)}"]
            else:
                xml_content = file_content

            # 1. Parse XML and technical validation (XSD)
            try:
                xml_etree = etree.fromstring(xml_content, parser=ValidationService._SECURE_PARSER)
                try:
                    detected_format, detected_flavor = detect_format(xml_etree)
                except Exception as e:
                    return False, None, None, [f"Format detection failed: {str(e)}"]
            except Exception as e:
                return False, None, None, [f"Invalid XML syntax: {str(e)}"]
            
            # XSD Check
            try:
                xml_check_xsd(xml_content, flavor=detected_format, level=detected_flavor)
            except Exception as e:
                return False, detected_format, detected_flavor, humanize_errors([str(e)])

            # 2. Business Rules Validation (Schematron Lite)
            if detected_flavor in ["en16931", "extended"]:
                if ValidationService._CORE_VALIDATOR:
                    schematron_errors = ValidationService._check_schematron(xml_etree, ValidationService._CORE_VALIDATOR)
                    if schematron_errors:
                        logger.warning(f"Business rule validation failed: {schematron_errors}")
                        # Errors are already humanized by message content usually, but we could wrap them
                        return False, detected_format, detected_flavor, schematron_errors

            logger.info("Complete validation (XSD + Business Rules) successful")
            return True, detected_format, detected_flavor, []
                
        except Exception as e:
            logger.exception(f"Unexpected error during validation: {e}")
            return False, None, None, [f"Unexpected validation error: {str(e)}"]
