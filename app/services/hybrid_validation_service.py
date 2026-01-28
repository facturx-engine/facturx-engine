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
from typing import Tuple, List, Optional, Dict, Any
from concurrent.futures import ProcessPoolExecutor, TimeoutError as FuturesTimeoutError
import asyncio

from facturx import get_xml_from_pdf, get_level, get_flavor
from lxml import etree

logger = logging.getLogger(__name__)

# Path configuration
PROJECT_ROOT = Path(__file__).parent.parent.parent
DOCS_ROOT = PROJECT_ROOT / "docs" / "2025_12_04_FNFE_SCHEMATRONS_FR_CTC_V1.2.0"

# Validation artifacts (relative to project)
XSD_PATH = DOCS_ROOT / "_CII_D22B_XSD" / "CrossIndustryInvoice_100pD22B.xsd"
XSLT_PATH = DOCS_ROOT / "_EN16931_Schematrons_V1.3.15_CII_ET_UBL" / "_XSLT" / "EN16931-CII-validation.xslt"

# ProcessPool configuration
_executor: Optional[ProcessPoolExecutor] = None
MAX_WORKERS = int(os.getenv("FX_VALIDATION_WORKERS", "2"))
VALIDATION_TIMEOUT = int(os.getenv("FX_VALIDATION_TIMEOUT", "30"))
MAX_TASKS_PER_CHILD = int(os.getenv("FX_MAX_TASKS_PER_CHILD", "100"))


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
    import sys
    import os
    
    # Add prototype path for imports
    proto_path = os.path.join(os.path.dirname(os.path.dirname(os.path.dirname(__file__))), 
                               "prototypes", "saxonc_validation")
    if proto_path not in sys.path:
        sys.path.insert(0, proto_path)
    
    from hybrid_validator import HybridValidator, ValidationResult
    
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
                result["format_detected"] = get_flavor(xml_etree)
                result["profile_detected"] = get_level(xml_etree)
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
            
            # 4. Run hybrid validation in process pool
            executor = _get_executor()
            
            try:
                future = executor.submit(
                    _run_hybrid_validation,
                    xml_content,
                    str(XSD_PATH),
                    str(XSLT_PATH)
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
