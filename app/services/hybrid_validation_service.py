"""
HybridValidationService: Production-grade EN 16931 validation using the Hybrid Architecture.

Uses:
- lxml for XSD structure validation (fast, secure)
- SaxonC-HE for Schematron business rules (XSLT 3.0 compliant)

This service is designed for use with ProcessPoolExecutor in production
to isolate SaxonC-HE and prevent memory issues.
"""
import logging
import os
from io import BytesIO
from pathlib import Path
from typing import Optional, Dict, Any
from concurrent.futures import ProcessPoolExecutor, TimeoutError as FuturesTimeoutError
import asyncio

from app.services.validation_utils import detect_format
from app.services.pdf_utils import get_xml_from_pdf
from lxml import etree

logger = logging.getLogger(__name__)

# Path configuration
PROJECT_ROOT = Path(__file__).parent.parent.parent
# Validation artifacts - Factur-X 1.08 / ZUGFeRD 2.4 (January 2026)
# Relocated to app/resources/schemas to avoid Windows MAX_PATH (260 chars) issues
SCHEMA_ROOT = PROJECT_ROOT / "app" / "resources" / "schemas"
XSD_PATH = SCHEMA_ROOT / "Factur-X_1.08_EN16931.xsd"
XSLT_PATH = SCHEMA_ROOT / "_XSLT_EN16931" / "FACTUR-X_EN16931.xslt"

# XRechnung 3.0.2
XRECHNUNG_30_ROOT = SCHEMA_ROOT / "xrechnung_3.0.2" / "cii"
XRECHNUNG_30_XSD = XRECHNUNG_30_ROOT / "xsd" / "CrossIndustryInvoice_100pD16B.xsd"
XRECHNUNG_30_XSLT = XRECHNUNG_30_ROOT / "xslt" / "XRechnung-CII-validation.xsl"

# ProcessPool configuration
_executor: Optional[ProcessPoolExecutor] = None
MAX_WORKERS = int(os.getenv("FX_VALIDATION_WORKERS", "2"))
VALIDATION_TIMEOUT = int(os.getenv("FX_VALIDATION_TIMEOUT", "30"))
MAX_TASKS_PER_CHILD = int(os.getenv("FX_MAX_TASKS_PER_CHILD", "100"))

# VeraPDF subprocess configuration
# Set VERAPDF_JAR=/app/bin/verapdf.jar in the Docker image (via ENV in Dockerfile)
VERAPDF_JAR = os.getenv("VERAPDF_JAR", "")


def _get_executor() -> ProcessPoolExecutor:
    """Get or create the validation process pool."""
    global _executor
    if _executor is None:
        _executor = ProcessPoolExecutor(
            max_workers=MAX_WORKERS,
            max_tasks_per_child=MAX_TASKS_PER_CHILD  # Recycle workers to prevent memory leaks
        )
        logger.info(f"Initialized HybridValidator ProcessPool with {MAX_WORKERS} workers (recycle every {MAX_TASKS_PER_CHILD} tasks)")
    return _executor


def _run_hybrid_validation(xml_content: bytes, xsd_path: str, xslt_path: str) -> Dict[str, Any]:
    """
    Worker function to run hybrid validation in an isolated process.
    
    This function is executed in a separate process to:
    1. Isolate SaxonC-HE memory from main process
    2. Prevent GIL contention
    3. Allow process recycling on memory issues
    """
    import os
    
    from app.services.hybrid_validator import HybridValidator
    
    try:
        validator = HybridValidator(
            xsd_path=xsd_path if os.path.exists(xsd_path) else None,
            xslt_path=xslt_path if os.path.exists(xslt_path) else None
        )
        
        result = validator.validate(xml_content)
        
        return {
            "is_valid": result.is_valid,
            "xsd_valid": result.xsd_valid,
            "schematron_valid": result.schematron_valid,
            "error_count": result.error_count,
            "warning_count": result.warning_count,
            "errors": [
                {
                    "rule_id": e.rule_id,
                    "message": e.message,
                    "location": e.location,
                    "severity": e.severity,
                    "layer": e.layer.value
                }
                for e in result.errors
            ]
        }
        
    except Exception as e:
        import traceback
        return {
            "is_valid": False,
            "error": str(e),
            "traceback": traceback.format_exc()
        }


class HybridValidationService:
    """
    Production-grade validation service using the Hybrid Architecture.
    
    Features:
    - XSD validation via lxml (structure)
    - Schematron validation via SaxonC-HE (business rules)
    - Process isolation for stability
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
    
    @classmethod
    def validate(cls, file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Validate a Factur-X PDF or XML file synchronously.
        
        Args:
            file_content: Raw file bytes
            filename: Original filename for type detection
            
        Returns:
            Dict with validation results
        """
        result = {
            "is_valid": False,
            "format_detected": None,
            "profile_detected": None,
            "xsd_valid": None,
            "schematron_valid": None,
            "pdfa_valid": None,
            "errors": [],
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
            # The EN16931 XSD and Schematron rules only apply to the EN16931 and EXTENDED profiles.
            # Applying them to MINIMUM/BASIC/BASICWL causes false negatives because those
            # profiles intentionally omit fields that are mandatory in EN16931:
            #   - XSD: requires IncludedSupplyChainTradeLineItem (absent in MINIMUM)
            #   - XSLT: requires line-item totals, VAT breakdowns, etc.
            # 
            # CRITICAL (Parity): EXTENDED is a technical superset of EN16931. 
            # Our current XSD (Factur-X_1.08_EN16931.xsd) is strictly EN16931 (Comfort) compliant.
            # Applying this XSD to EXTENDED causes false negatives on valid Extended elements
            # like TaxApplicableTradeCurrencyExchange (Fremdwährung).
            # For EXTENDED: We skip XSD validation (structural) but KEEP Schematron (Business rules).
            
            detected_profile = result.get("profile_detected", "").lower()
            detected_format = result.get("format_detected", "").lower()
            
            effective_xsd_path = ""   # Default: Skip XSD
            effective_xslt_path = ""  # Default: Skip XSLT
            
            # 4.1 Handle UBL (Partial Support Note)
            if detected_format == "ubl":
                # Currently we only have CII assets for XRechnung.
                # UBL requires a different XSD/XSLT stack.
                result["errors"].append({
                    "rule_id": "FX-UBL-PARTIAL",
                    "message": f"Format UBL ({detected_profile}) détecté. La validation des règles métier (Schematron) pour UBL n'est pas encore activée.",
                    "severity": "warning",
                    "layer": "system"
                })
                # We skip further hybrid validation to avoid applying CII rules to UBL
                result["is_valid"] = True # Structure is valid if it parsed
                return result

            # 4.2 Handle CII / Factur-X
            if detected_profile == "en16931":
                effective_xsd_path = str(XSD_PATH)
                effective_xslt_path = str(XSLT_PATH)
                logger.info(f"Profile '{detected_profile}': applying full EN16931 XSD + Schematron rules")
            elif detected_profile == "extended":
                # Extended is a superset. We use the specific EXTENDED XSLT which includes
                # the necessary relaxations for Extended features (Foreign Currency, etc.)
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
            
            # 5. Run hybrid validation in process pool
            executor = _get_executor()
            
            try:
                future = executor.submit(
                    _run_hybrid_validation,
                    xml_content,
                    effective_xsd_path,
                    effective_xslt_path
                )
                validation_result = future.result(timeout=VALIDATION_TIMEOUT)
                
                if "error" in validation_result:
                    result["errors"].append({
                        "rule_id": "FX-HYBRID-ERROR",
                        "message": validation_result["error"],
                        "severity": "error",
                        "layer": "system"
                    })
                    return result
                
                result["is_valid"] = validation_result["is_valid"]
                result["xsd_valid"] = validation_result["xsd_valid"]
                result["schematron_valid"] = validation_result["schematron_valid"]
                result["errors"] = validation_result["errors"]
                
            except FuturesTimeoutError:
                result["errors"].append({
                    "rule_id": "FX-TIMEOUT",
                    "message": f"Validation timed out after {VALIDATION_TIMEOUT}s",
                    "severity": "error",
                    "layer": "system"
                })
            except Exception as e:
                result["errors"].append({
                    "rule_id": "FX-POOL-ERROR",
                    "message": f"Process pool error: {e}",
                    "severity": "error",
                    "layer": "system"
                })

            # 6. PDF/A-3b validation via VeraPDF subprocess (PDF inputs only)
            # Runs in the main process as an isolated subprocess — no memory leaks.
            # Skipped gracefully when VERAPDF_JAR is not configured (dev/test environments).
            if is_pdf:
                if VERAPDF_JAR and os.path.exists(VERAPDF_JAR):
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
                        # pdfa_valid stays None — caller can distinguish from explicit False
                elif VERAPDF_JAR:
                    logger.warning("VERAPDF_JAR configured but not found: %s", VERAPDF_JAR)

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
    async def validate_async(cls, file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Validate a Factur-X PDF or XML file asynchronously.
        
        Uses run_in_executor to offload to the process pool without blocking.
        """
        loop = asyncio.get_running_loop()
        
        # Offload the entire validation to avoid blocking
        return await loop.run_in_executor(
            None,  # Default thread pool for the sync wrapper
            cls.validate,
            file_content,
            filename
        )


def shutdown_executor():
    """Cleanup function to shutdown the process pool gracefully."""
    global _executor
    if _executor:
        _executor.shutdown(wait=True)
        _executor = None
        logger.info("HybridValidator ProcessPool shutdown complete")
