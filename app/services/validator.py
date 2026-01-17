"""
XML validation service using xmlschema and factur-x library.
"""
import logging
from io import BytesIO
from typing import Tuple, Optional
from facturx import get_xml_from_pdf, xml_check_xsd, get_level, get_flavor
from lxml import etree

logger = logging.getLogger(__name__)


class ValidationService:
    """Service for validating Factur-X/ZUGFeRD files."""

    @staticmethod
    def validate_file(file_content: bytes, filename: str) -> Tuple[bool, Optional[str], Optional[str], list[str]]:
        """
        Validate a Factur-X PDF or XML file.
        
        Args:
            file_content: Raw file bytes.
            filename: Original filename (used for type detection).
            
        Returns:
            Tuple of (is_valid, format, flavor, errors_list).
        """
        errors = []
        detected_format = None
        detected_flavor = None
        
        try:
            # Detect file type
            is_pdf = filename.lower().endswith('.pdf') or file_content.startswith(b'%PDF')
            
            if is_pdf:
                # Extract XML from PDF
                logger.info(f"Detected PDF file: {filename}")
                try:
                    # get_xml_from_pdf returns a tuple: (xml_filename, xml_bytes)
                    xml_filename, xml_content = get_xml_from_pdf(
                        BytesIO(file_content),
                        check_xsd=False  # We'll validate separately
                    )
                    if not xml_content or not xml_filename:
                        return False, None, None, ["No Factur-X/ZUGFeRD XML found in PDF"]
                    
                    logger.info(f"Successfully extracted XML from PDF: {xml_filename}")
                    
                except Exception as e:
                    logger.error(f"Failed to extract XML from PDF: {e}")
                    return False, None, None, [f"Failed to extract XML from PDF: {str(e)}"]
            else:
                # Assume it's raw XML
                logger.info(f"Detected XML file: {filename}")
                xml_content = file_content
            
            # Parse XML to detect flavor and level
            try:
                xml_etree = etree.fromstring(xml_content)
                detected_format = get_flavor(xml_etree)
                detected_flavor = get_level(xml_etree, detected_format)
                logger.info(f"Detected format: {detected_format}, flavor: {detected_flavor}")
            except Exception as e:
                logger.error(f"Failed to parse XML: {e}")
                return False, None, None, [f"Invalid XML syntax: {str(e)}"]
            
            # Validate against XSD
            try:
                xml_check_xsd(
                    xml_content,
                    flavor=detected_format,
                    level=detected_flavor
                )
                logger.info("XML validation successful")
                return True, detected_format, detected_flavor, []
                
            except Exception as e:
                error_msg = str(e)
                logger.error(f"XSD validation failed: {error_msg}")
                errors.append(error_msg)
                return False, detected_format, detected_flavor, errors
                
        except Exception as e:
            logger.exception(f"Unexpected error during validation: {e}")
            return False, None, None, [f"Unexpected validation error: {str(e)}"]
