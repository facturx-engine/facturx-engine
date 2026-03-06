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

# Factur-X 1.08 BASICWL (XSD structure validation)
BASICWL_XSD_PATH = SCHEMA_ROOT / "Factur-X_1.08_BASICWL.xsd"

# XRechnung 3.0.2 — CII (Cross-Industry Invoice)
XRECHNUNG_30_ROOT = SCHEMA_ROOT / "xrechnung_3.0.2" / "cii"
XRECHNUNG_30_XSD = XRECHNUNG_30_ROOT / "xsd" / "CrossIndustryInvoice_100pD16B.xsd"
XRECHNUNG_30_XSLT = XRECHNUNG_30_ROOT / "xslt" / "XRechnung-CII-validation.xsl"

# XRechnung 3.0.2 — UBL (R2)
# Place XRechnung-UBL-validation.xsl here (from xrechnung-schematron release on KoSIT GitHub).
# When the file is absent, the service gracefully falls back to EN16931-UBL Schematron.
XRECHNUNG_30_UBL_ROOT = SCHEMA_ROOT / "xrechnung_3.0.2" / "ubl"
XRECHNUNG_30_UBL_XSLT = XRECHNUNG_30_UBL_ROOT / "xslt" / "XRechnung-UBL-validation.xsl"

# EN16931 UBL Schematron — base rules for UBL (Peppol BIS 3.0, generic UBL invoices)
UBL_EN16931_XSLT = SCHEMA_ROOT / "_XSLT_EN16931_UBL" / "EN16931-UBL-validation.xslt"

# UBL 2.1 XSD — OASIS structural schemas (R5)
# Place the OASIS UBL-2.1.zip maindoc content at app/resources/schemas/ubl-2.1/xsd/maindoc/
# When absent, XSD structural validation for UBL is skipped (Schematron still runs).
UBL_XSD_INVOICE_PATH = SCHEMA_ROOT / "ubl-2.1" / "xsd" / "maindoc" / "UBL-Invoice-2.1.xsd"
UBL_XSD_CREDITNOTE_PATH = SCHEMA_ROOT / "ubl-2.1" / "xsd" / "maindoc" / "UBL-CreditNote-2.1.xsd"

# French regulatory rules — BR-FR CTC v1.2.0 (France 2026 mandate / Chorus Pro parity)
BR_FR_CTC_ROOT = SCHEMA_ROOT / "_BR_FR_CTC"
BR_FR_CTC_CII_XSLT = BR_FR_CTC_ROOT / "BR-FR-CII.xsl"
BR_FR_CTC_UBL_XSLT = BR_FR_CTC_ROOT / "BR-FR-UBL.xsl"

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
            "validation_mode": "hybrid",  # vs "lite" for Community fallback
            "layers_executed": [],
            "layers_skipped": [],
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
                result["layers_skipped"].append({"layer": "xsd", "reason": "artifact_missing"})
                result["layers_skipped"].append({"layer": "schematron", "reason": "artifact_missing"})
                result["validation_completeness"] = "partial"
                return result
            
            # 4. Profile-aware schema selection
            detected_profile = result.get("profile_detected", "").lower()
            detected_format = result.get("format_detected", "").lower()
            
            effective_xsd_path = ""   # Default: Skip XSD
            effective_xslt_path = ""  # Default: Skip XSLT
            
            # 4.1 Handle UBL documents (Invoice or CreditNote)
            if detected_format == "ubl":
                # Detect document type from XML root tag for XSD selection (R5)
                root_tag = xml_etree.tag
                is_credit_note_ubl = "CreditNote" in root_tag

                # R5: Optional UBL 2.1 XSD structural validation (OASIS)
                ubl_xsd_candidate = UBL_XSD_CREDITNOTE_PATH if is_credit_note_ubl else UBL_XSD_INVOICE_PATH
                if ubl_xsd_candidate.exists():
                    effective_xsd_path = str(ubl_xsd_candidate)
                    logger.info(f"UBL XSD found — applying structural validation ({ubl_xsd_candidate.name})")
                else:
                    logger.debug("UBL 2.1 XSD not present — skipping structural XSD validation (Schematron only)")

                # R2: XRechnung UBL — prefer dedicated KoSIT Schematron, fall back to EN16931-UBL
                if detected_profile == "xrechnung_3.0":
                    if XRECHNUNG_30_UBL_XSLT.exists():
                        effective_xslt_path = str(XRECHNUNG_30_UBL_XSLT)
                        logger.info("UBL Profile 'xrechnung_3.0': applying XRechnung 3.0.2 UBL Schematron rules")
                    else:
                        effective_xslt_path = str(UBL_EN16931_XSLT)
                        logger.warning(
                            "XRechnung UBL Schematron not found at %s — "
                            "falling back to EN16931-UBL base rules. "
                            "Place XRechnung-UBL-validation.xsl from the KoSIT xrechnung-schematron release "
                            "at app/resources/schemas/xrechnung_3.0.2/ubl/xslt/ to enable full XRechnung UBL validation.",
                            XRECHNUNG_30_UBL_XSLT
                        )
                else:
                    # EN16931-UBL, Peppol BIS 3.0, or unknown UBL profile → EN16931 base rules
                    effective_xslt_path = str(UBL_EN16931_XSLT)
                    logger.info(f"UBL Profile '{detected_profile}': applying EN16931 UBL Schematron rules")

            # 4.2 Handle CII / Factur-X
            elif detected_profile == "en16931":
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
                effective_xsd_path = str(BASICWL_XSD_PATH)
                effective_xslt_path = str(SCHEMA_ROOT / "_XSLT_BASICWL" / "FACTUR-X_BASIC-WL.xslt")
                logger.info(f"Profile '{detected_profile}': applying BASICWL XSD + Schematron rules")
            elif detected_profile == "xrechnung_3.0":
                effective_xsd_path = str(XRECHNUNG_30_XSD)
                effective_xslt_path = str(XRECHNUNG_30_XSLT)
                logger.info(f"Profile '{detected_profile}': applying XRechnung 3.0.2 XSD + Schematron rules")
            else:
                logger.info(f"Profile '{detected_profile}': no specific rules found (Structural Validation Only)")
            
            # 5. Run hybrid validation directly (no ProcessPool)
            has_xsd = effective_xsd_path and os.path.exists(effective_xsd_path)
            has_xslt = effective_xslt_path and os.path.exists(effective_xslt_path)
            has_saxon = SAXON_JAR and os.path.exists(SAXON_JAR)

            try:
                validator = HybridValidator(
                    xsd_path=effective_xsd_path if has_xsd else None,
                    xslt_path=effective_xslt_path if has_xslt else None,
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

                # --- Layer tracking ---
                if has_xsd:
                    result["layers_executed"].append("xsd")
                elif effective_xsd_path:
                    # Path was selected but file doesn't exist
                    result["layers_skipped"].append({"layer": "xsd", "reason": "artifact_missing"})

                if has_xslt and has_saxon:
                    result["layers_executed"].append("schematron")
                elif has_xslt and not has_saxon:
                    result["layers_skipped"].append({"layer": "schematron", "reason": "tool_missing:saxon_jar"})
                elif not has_xslt and effective_xslt_path:
                    result["layers_skipped"].append({"layer": "schematron", "reason": "artifact_missing:xslt"})
                
            except Exception as e:
                result["errors"].append({
                    "rule_id": "FX-HYBRID-ERROR",
                    "message": f"Core validation failed: {str(e)}",
                    "severity": "error",
                    "layer": "system"
                })
                return result

            # 5.5 French regulatory rules — BR-FR CTC v1.2.0
            # Activated when the seller's country is France (FR), Saxon-HE is available,
            # and the BR-FR XSLT artifacts exist.
            try:
                seller_country = cls._extract_seller_country(xml_content, detected_format)
                if seller_country == "FR":
                    fr_xslt = BR_FR_CTC_CII_XSLT if detected_format != "ubl" else BR_FR_CTC_UBL_XSLT
                    if fr_xslt.exists() and SAXON_JAR and os.path.exists(SAXON_JAR):
                        logger.info("Seller country is FR — applying BR-FR CTC v1.2.0 rules")
                        fr_validator = HybridValidator(
                            xsd_path=None,
                            xslt_path=str(fr_xslt),
                            saxon_jar=SAXON_JAR
                        )
                        fr_result = fr_validator.validate(xml_content)
                        for e in fr_result.errors:
                            result["errors"].append({
                                "rule_id": e.rule_id,
                                "message": e.message,
                                "location": e.location,
                                "severity": e.severity,
                                "layer": e.layer.value,
                            })
                        if not fr_result.schematron_valid:
                            result["is_valid"] = False
                        result["layers_executed"].append("br_fr_ctc")
                    else:
                        logger.debug("BR-FR CTC skipped: Saxon JAR or XSLT not available")
                        if not has_saxon:
                            result["layers_skipped"].append({"layer": "br_fr_ctc", "reason": "tool_missing:saxon_jar"})
                        elif not fr_xslt.exists():
                            result["layers_skipped"].append({"layer": "br_fr_ctc", "reason": "artifact_missing"})
                # seller_country != "FR" → br_fr_ctc is not applicable, don't add to skipped
            except Exception as fr_ex:
                logger.warning(f"BR-FR CTC validation failed (non-blocking): {fr_ex}")

            # 6. PDF/A-3b validation via VeraPDF subprocess (PDF inputs only)
            # VeraPDF is strictly a Pro feature (Evaluation, Business, Enterprise).
            if is_pdf:
                from app.license import has_tier
                if has_tier(["Evaluation", "Pro"]):
                    # Check both global (Ops) and request-level (Dev) toggles
                    if not cls.VERAPDF_ENABLED_GLOBAL:
                        logger.info("VeraPDF validation skipped: Globally disabled via VERAPDF_ENABLED=false")
                        result["pdfa_valid"] = None
                        result["layers_skipped"].append({"layer": "pdfa3b", "reason": "disabled_by_config"})
                    elif not validate_pdfa:
                        logger.info("VeraPDF validation skipped: Disabled per-request via validate_pdfa=false")
                        result["pdfa_valid"] = None
                        result["layers_skipped"].append({"layer": "pdfa3b", "reason": "disabled_by_request"})
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
                            result["layers_executed"].append("pdfa3b")
                        except Exception as e:
                            logger.error("VeraPDF integration error: %s", e)
                    else:
                        if VERAPDF_JAR:
                            logger.warning("VERAPDF_JAR configured but not found: %s", VERAPDF_JAR)
                        result["layers_skipped"].append({"layer": "pdfa3b", "reason": "tool_missing:verapdf_jar"})
                else:
                    logger.info("VeraPDF validation skipped: Requires Pro license.")
                    result["pdfa_valid"] = None  # Indicate it was not run
                    result["layers_skipped"].append({"layer": "pdfa3b", "reason": "license_required"})

            # 7. Compute validation_completeness
            result["validation_completeness"] = "partial" if result["layers_skipped"] else "full"

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
    
    @staticmethod
    def _extract_seller_country(xml_content: bytes, detected_format: str) -> str:
        """
        Extract the seller's country code from the invoice XML.
        Returns an ISO 3166-1 alpha-2 code (e.g. 'FR', 'DE') or '' if not found.
        """
        try:
            secure_parser = etree.XMLParser(resolve_entities=False, no_network=True, recover=True)
            root = etree.fromstring(xml_content, parser=secure_parser)
            if detected_format == "ubl":
                nodes = root.xpath(
                    "//*[local-name()='AccountingSupplierParty']"
                    "//*[local-name()='Country']"
                    "/*[local-name()='IdentificationCode']"
                )
            else:
                # CII
                nodes = root.xpath(
                    "//*[local-name()='SellerTradeParty']"
                    "/*[local-name()='PostalTradeAddress']"
                    "/*[local-name()='CountryID']"
                )
            if nodes and nodes[0].text:
                return nodes[0].text.strip().upper()
        except Exception:
            pass
        return ""

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
