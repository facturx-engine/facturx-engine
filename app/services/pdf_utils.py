"""
Shared PDF XML extraction utility.

Wraps the upstream `facturx.get_xml_from_pdf` with fallback support for
additional attachment names (e.g., `xrechnung.xml`) that the library
does not natively recognize.
"""
import logging
from io import BytesIO
from typing import Optional, Tuple

import pypdf
from facturx import get_xml_from_pdf as _upstream_get_xml_from_pdf

logger = logging.getLogger(__name__)

# Additional attachment names to look for when the upstream library
# fails to find embedded XML. Ordered by priority.
_FALLBACK_ATTACHMENT_NAMES = [
    "xrechnung.xml",
]


def is_pdfa3b(pdf_bytes: bytes) -> bool:
    """
    Lightweight heuristic: returns True if the PDF declares PDF/A-3b conformance
    in its XMP metadata (pdfaid:part=3, pdfaid:conformance=B).

    Not a substitute for VeraPDF (Pro). Used to gate /merge for Community.
    Returns False on any error or missing metadata.
    """
    try:
        reader = pypdf.PdfReader(BytesIO(pdf_bytes))
        xmp = reader.xmp_metadata
        if xmp is None:
            return False
        return str(xmp.pdfaid_part) == "3" and str(xmp.pdfaid_conformance).upper() == "B"
    except Exception:
        return False


def get_xml_from_pdf(pdf_input, check_xsd=False, check_schematron=False, **kwargs) -> Tuple[Optional[str], Optional[bytes]]:
    """
    Extract XML from a Factur-X/ZUGFeRD/XRechnung PDF.

    First tries the upstream `facturx.get_xml_from_pdf`. If that returns
    empty XML, falls back to scanning PDF attachments for known invoice
    XML filenames (e.g., `xrechnung.xml`).

    Args:
        pdf_input: BytesIO or file-like object containing the PDF.
        **kwargs: Passed through to upstream (e.g., check_xsd=False).

    Returns:
        Tuple of (xml_filename, xml_bytes). Returns (None, None) if no
        XML is found.
    """
    if isinstance(pdf_input, bytes):
        pdf_input = BytesIO(pdf_input)

    # Ensure we can re-read the stream after upstream tries
    if isinstance(pdf_input, BytesIO):
        start_pos = pdf_input.tell()
    else:
        start_pos = None

    # 1. Try upstream first (handles factur-x.xml, zugferd-invoice.xml)
    try:
        xml_filename, xml_content = _upstream_get_xml_from_pdf(
            pdf_input, check_xsd=check_xsd, **kwargs
        )
        if xml_content:
            return xml_filename, xml_content
    except Exception as e:
        logger.debug(f"Upstream get_xml_from_pdf failed: {e}")

    # 2. Fallback: scan PDF attachments via pypdf
    logger.info("Upstream extraction returned no XML — trying fallback attachment scan")

    # Reset stream position
    if start_pos is not None:
        pdf_input.seek(start_pos)
    elif hasattr(pdf_input, 'seek'):
        pdf_input.seek(0)

    try:
        reader = pypdf.PdfReader(pdf_input)

        for attach_name in _FALLBACK_ATTACHMENT_NAMES:
            if attach_name in reader.attachments:
                items = reader.attachments[attach_name]
                if items:
                    xml_bytes = items[0]  # First attachment with that name
                    logger.info(f"Fallback: found '{attach_name}' attachment ({len(xml_bytes)} bytes)")
                    return attach_name, xml_bytes

        # Also scan all attachments for any .xml file as last resort
        for name, items in reader.attachments.items():
            if name.lower().endswith('.xml') and items:
                logger.info(f"Fallback: found unexpected XML attachment '{name}' ({len(items[0])} bytes)")
                return name, items[0]

    except Exception as e:
        logger.warning(f"Fallback attachment extraction failed: {e}")

    return None, None
