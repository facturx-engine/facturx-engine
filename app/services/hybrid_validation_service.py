"""
HybridValidationService: Production-grade EN 16931 validation using the Hybrid Architecture.

Uses:
- lxml for XSD structure validation (fast, secure)
- Saxon-HE Subprocess for Schematron business rules (Zero memory leaks)
"""
import logging
import os
from io import BytesIO
from pathlib import Path
from typing import Dict, Any
import asyncio

from app.services.validation_utils import detect_format
from app.services.pdf_utils import get_xml_from_pdf
from lxml import etree
from app.services.hybrid_validator import HybridValidator

logger = logging.getLogger(__name__)

# Path configuration
PROJECT_ROOT = Path(__file__).parent.parent.parent
# Validation artifacts - Factur-X 1.08 / ZUGFeRD 2.4 (January 2026)
SCHEMA_ROOT = PROJECT_ROOT / "app" / "resources" / "schemas"
XSD_PATH = SCHEMA_ROOT / "Factur-X_1.08_EN16931.xsd"
XSLT_PATH = SCHEMA_ROOT / "_XSLT_EN16931" / "FACTUR-X_EN16931.xslt"

# XRechnung 3.0.2
XRECHNUNG_30_ROOT = SCHEMA_ROOT / "xrechnung_3.0.2" / "cii"
XRECHNUNG_30_XSD = XRECHNUNG_30_ROOT / "xsd" / "CrossIndustryInvoice_100pD16B.xsd"
XRECHNUNG_30_XSLT = XRECHNUNG_30_ROOT / "xslt" / "XRechnung-CII-validation.xsl"

VALIDATION_TIMEOUT = int(os.getenv("FX_VALIDATION_TIMEOUT", "30"))

# Subprocess Java configurations
VERAPDF_JAR = os.getenv("VERAPDF_JAR", "")
SAXON_JAR = os.getenv("SAXON_JAR", "")

class HybridValidationService:
    """
    Production-grade validation service using the Hybrid Architecture.
    
    Features:
    - XSD validation via lxml (structure)
    - Schematron validation via Saxon-HE subprocess (business rules)
    - Async-compatible for FastAPI
    
    Usage:
        # In FastAPI endpoint
        result = await HybridValidationService.validate_async(file_content, filename)
        
        # Synchronous
        result = HybridValidationService.validate(file_content, filename)
    """
    
    # Secure parser for PDF extraction
    _SECURE_PARSER = etree.XMLParser(
        resolve_entities=False,
        no_network=True,
        huge_tree=False,
        recover=False
    )
    
    # Global Ops Switch for VeraPDF (Default: True)
    VERAPDF_ENABLED_GLOBAL = os.getenv("VERAPDF_ENABLED", "true").lower() == "true"
    
    @classmethod
    def validate(cls, file_content: bytes, filename: str, validate_pdfa: bool = True) -> Dict[str, Any]:
        """
        Validate a Factur-X PDF or XML file synchronously.
        """
        result = {
            "is_valid": False,
            "format_detected": None,
            "profile_detected": None,
            "xsd_valid": None,
            "schematron_valid": None,
            "pdfa_valid": None,
            "errors": [],
            "xml_content": None,
            "validation_mode": "hybrid"  # vs "lite" for Community fallback
        }
        
        try:
            # 1. Extract XML if PDF
            is_pdf = filename.lower().endswith('.pdf') or file_content.startswith(b'%PDF')
            
            if is_pdf:
                try:
                    xml_filename, xml_content = get_xml_from_pdf(
                        BytesIO(file_content),
                        check_xsd=False
                    )
                    if not xml_content:
                        result["errors"].append({
                            "rule_id": "FX-NO-XML",
                            "message": "No Factur-X/ZUGFeRD XML found in PDF",
                            "severity": "error",
                            "layer": "system"
                        })
                        return result
                    result["xml_content"] = xml_content
                except Exception as e:
                    result["errors"].append({
                        "rule_id": "FX-EXTRACT-FAIL",
                        "message": f"Failed to extract XML: {e}",
                        "severity": "error",
                        "layer": "system"
                    })
                    return result
            else:
                xml_content = file_content
                result["xml_content"] = xml_content
            
            # 2. Detect format/profile
            try:
                xml_etree = etree.fromstring(xml_content, parser=cls._SECURE_PARSER)
                result["format_detected"], result["profile_detected"] = detect_format(xml_etree)
            except Exception as e:
                result["errors"].append({
                    "rule_id": "FX-PARSE-ERROR",
                    "message": f"Invalid XML: {e}",
                    "severity": "error",
                    "layer": "xsd"
                })
                return result
            
            # 3. Check if hybrid validation is available
            xsd_available = XSD_PATH.exists()
            xslt_available = XSLT_PATH.exists()
            
            if not xsd_available and not xslt_available:
                logger.warning("No validation schemas found - falling back to basic validation")
                result["validation_mode"] = "lite"
                result["is_valid"] = True  # Basic parse succeeded
                return result
            
            # 4. Profile-aware schema selection
            detected_profile = result.get("profile_detected", "").lower()
            detected_format = result.get("format_detected", "").lower()
            
            effective_xsd_path = ""   # Default: Skip XSD
            effective_xslt_path = ""  # Default: Skip XSLT
            
            # 4.1 Handle UBL (Partial Support Note)
            if detected_format == "ubl":
                result["errors"].append({
                    "rule_id": "FX-UBL-PARTIAL",
                    "message": f"Format UBL ({detected_profile}) détecté. La validation des règles métier (Schematron) pour UBL n'est pas encore activée.",
                    "severity": "warning",
                    "layer": "system"
                })
                result["is_valid"] = True # Structure is valid if it parsed
                return result

            # 4.2 Handle CII / Factur-X
            if detected_profile == "en16931":
                effective_xsd_path = str(XSD_PATH)
                effective_xslt_path = str(XSLT_PATH)
                logger.info(f"Profile '{detected_profile}': applying full EN16931 XSD + Schematron rules")
            elif detected_profile == "extended":
                effective_xsd_path = "" # Still skip XSD as it is too strict (EN16931)
                effective_xslt_path = str(SCHEMA_ROOT / "_XSLT_EXTENDED" / "FACTUR-X_EXTENDED.xslt")
                logger.info(f"Profile '{detected_profile}': applying EXTENDED Schematron rules")
            elif detected_profile == "basic":
                effective_xslt_path = str(SCHEMA_ROOT / "_XSLT_BASIC" / "FACTUR-X_BASIC.xslt")
                logger.info(f"Profile '{detected_profile}': applying BASIC Schematron rules")
            elif detected_profile == "minimum":
                effective_xslt_path = str(SCHEMA_ROOT / "_XSLT_MINIMUM" / "FACTUR-X_MINIMUM.xslt")
                logger.info(f"Profile '{detected_profile}': applying MINIMUM Schematron rules")
            elif detected_profile in ("basicwl", "basic wl"):
                effective_xslt_path = str(SCHEMA_ROOT / "_XSLT_BASICWL" / "FACTUR-X_BASIC-WL.xslt")
                logger.info(f"Profile '{detected_profile}': applying BASIC WL Schematron rules")
            elif detected_profile == "xrechnung_3.0":
                effective_xsd_path = str(XRECHNUNG_30_XSD)
                effective_xslt_path = str(XRECHNUNG_30_XSLT)
                logger.info(f"Profile '{detected_profile}': applying XRechnung 3.0.2 XSD + Schematron rules")
            else:
                logger.info(f"Profile '{detected_profile}': no specific rules found (Structural Validation Only)")
            
            # 5. Run hybrid validation directly (no ProcessPool)
            try:
                validator = HybridValidator(
                    xsd_path=effective_xsd_path if os.path.exists(effective_xsd_path) else None,
                    xslt_path=effective_xslt_path if os.path.exists(effective_xslt_path) else None,
                    saxon_jar=SAXON_JAR
                )
                
                validation_result = validator.validate(xml_content)
                
                result["is_valid"] = validation_result.is_valid
                result["xsd_valid"] = validation_result.xsd_valid
                result["schematron_valid"] = validation_result.schematron_valid
                result["errors"].extend([
                    {
                        "rule_id": e.rule_id,
                        "message": e.message,
                        "location": e.location,
                        "severity": e.severity,
                        "layer": e.layer.value
                    }
                    for e in validation_result.errors
                ])
                
            except Exception as e:
                result["errors"].append({
                    "rule_id": "FX-HYBRID-ERROR",
                    "message": f"Core validation failed: {str(e)}",
                    "severity": "error",
                    "layer": "system"
                })
                return result

            # 6. PDF/A-3b validation via VeraPDF subprocess (PDF inputs only)
            # VeraPDF is strictly a Pro feature (Evaluation, Business, Enterprise).
            if is_pdf:
                from app.license import has_tier
                if has_tier(["Evaluation", "Pro"]):
                    # Check both global (Ops) and request-level (Dev) toggles
                    if not cls.VERAPDF_ENABLED_GLOBAL:
                        logger.info("VeraPDF validation skipped: Globally disabled via VERAPDF_ENABLED=false")
                        result["pdfa_valid"] = None
                    elif not validate_pdfa:
                        logger.info("VeraPDF validation skipped: Disabled per-request via validate_pdfa=false")
                        result["pdfa_valid"] = None
                    elif VERAPDF_JAR and os.path.exists(VERAPDF_JAR):
                        try:
                            from app.services.hybrid_validator import validate_pdfa3
                            pdfa_valid, pdfa_errors = validate_pdfa3(file_content, VERAPDF_JAR)
                            result["pdfa_valid"] = pdfa_valid
                            for e in pdfa_errors:
                                result["errors"].append({
                                    "rule_id": e.rule_id,
                                    "message": e.message,
                                    "location": e.location,
                                    "severity": e.severity,
                                    "layer": e.layer.value,
                                })
                            if pdfa_valid is False:
                                result["is_valid"] = False
                        except Exception as e:
                            logger.error("VeraPDF integration error: %s", e)
                    elif VERAPDF_JAR:
                        logger.warning("VERAPDF_JAR configured but not found: %s", VERAPDF_JAR)
                else:
                    logger.info("VeraPDF validation skipped: Requires Pro license.")
                    result["pdfa_valid"] = None # Indicate it was not run
                    

            return result
            
        except Exception as e:
            logger.exception(f"Unexpected validation error: {e}")
            result["errors"].append({
                "rule_id": "FX-INTERNAL",
                "message": f"Internal error: {e}",
                "severity": "error",
                "layer": "system"
            })
            return result
    
    @classmethod
    async def validate_async(cls, file_content: bytes, filename: str, validate_pdfa: bool = True) -> Dict[str, Any]:
        """
        Validate a Factur-X PDF or XML file asynchronously.
        
        Uses run_in_executor with default ThreadPool to prevent blocking the event loop natively.
        """
        loop = asyncio.get_running_loop()
        
        # Offload validation to default ThreadPool since Java subprocess internally does the heavy lifting.
        return await loop.run_in_executor(
            None,
            cls.validate,
            file_content,
            filename,
            validate_pdfa
        )
