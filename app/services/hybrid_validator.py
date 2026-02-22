import logging
import os
import subprocess
import tempfile
from dataclasses import dataclass
from enum import Enum
from typing import List, Optional, Tuple

from lxml import etree
from saxonche import PySaxonProcessor

logger = logging.getLogger(__name__)

class ValidationLayer(Enum):
    XSD = "xsd"
    SCHEMATRON = "schematron"
    PDF_A = "pdf_a"
    SYSTEM = "system"

VERAPDF_MRR_NS = "http://www.verapdf.org/MachineReadableReport"

@dataclass
class ValidationError:
    rule_id: str
    message: str
    location: str
    severity: str
    layer: ValidationLayer

@dataclass
class ValidationResult:
    is_valid: bool
    xsd_valid: bool
    schematron_valid: bool
    errors: List[ValidationError]
    
    @property
    def error_count(self) -> int:
        return len([e for e in self.errors if e.severity.lower() in ("error", "fatal")])
    
    @property
    def warning_count(self) -> int:
        return len([e for e in self.errors if e.severity.lower() == "warning"])

class HybridValidator:
    """
    Hybrid Validation Engine:
    - XSD: lxml (fast, standard)
    - Schematron: SaxonC-HE (official EU rules, XSLT 3.0)
    """
    def __init__(self, xsd_path: Optional[str] = None, xslt_path: Optional[str] = None):
        self.xsd_path = xsd_path
        self.xslt_path = xslt_path

    def validate(self, xml_content: bytes) -> ValidationResult:
        errors = []
        xsd_valid = True
        schematron_valid = True
        
        # 1. XSD Validation via lxml
        if self.xsd_path and os.path.exists(self.xsd_path):
            try:
                # Security: Load XSD directly from file path to ensure relative imports resolve correctly
                # etree.XMLSchema(file=path) handles base_url properly for nested imports
                schema = etree.XMLSchema(file=self.xsd_path)
                
                # Parse XML to validate
                parser = etree.XMLParser(resolve_entities=False, no_network=True)
                doc = etree.fromstring(xml_content, parser=parser)
                
                if not schema.validate(doc):
                    xsd_valid = False
                    for err in schema.error_log:
                        errors.append(ValidationError(
                            rule_id="XSD-INVALID",
                            message=err.message,
                            location=f"Line {err.line}, Col {err.column}",
                            severity="error",
                            layer=ValidationLayer.XSD
                        ))
            except Exception as e:
                logger.error(f"XSD Engine Error: {e}")
                errors.append(ValidationError("SYS-XSD", str(e), "", "error", ValidationLayer.SYSTEM))
                xsd_valid = False

        # 2. Schematron Validation via SaxonC-HE
        if self.xslt_path and os.path.exists(self.xslt_path):
            try:
                # We use a context manager to ensure Saxon resources are released
                # Note: ProcessPool isolation handles memory management at a higher level
                with PySaxonProcessor(license=False) as proc:
                    # Security: Hardening against external entities
                    proc.set_configuration_property("http://saxon.sf.net/feature/parserFeature?uri=http://xml.org/sax/features/external-general-entities", "false")
                    proc.set_configuration_property("http://saxon.sf.net/feature/parserFeature?uri=http://xml.org/sax/features/external-parameter-entities", "false")
                    
                    xsltproc = proc.new_xslt30_processor()
                    executable = xsltproc.compile_stylesheet(stylesheet_file=self.xslt_path)
                    
                    # Run transformation
                    # Use utf-8-sig to automatically strip BOM if present (Common in official FNFE examples)
                    xml_text = xml_content.decode('utf-8-sig')
                    input_node = proc.parse_xml(xml_text=xml_text)

                    svrl_result = executable.transform_to_string(xdm_node=input_node)
                    
                    # Parse SVRL (Schematron Validation Report Language)
                    svrl_doc = etree.fromstring(svrl_result.encode('utf-8'))
                    ns = {"svrl": "http://purl.oclc.org/dsdl/svrl"}
                    
                    failed_asserts = svrl_doc.xpath("//svrl:failed-assert", namespaces=ns)
                    for fa in failed_asserts:
                        role = (fa.get("role") or "error").lower()
                        # Blocking errors: error, fatal, or undefined
                        is_error = role in ("error", "fatal")
                        
                        if is_error:
                            schematron_valid = False
                        
                        text_nodes = fa.xpath("svrl:text", namespaces=ns)
                        msg = text_nodes[0].text if text_nodes else "Rule violation"
                        
                        errors.append(ValidationError(
                            rule_id=fa.get("id", "RULE-FAIL"),
                            message=msg.strip(),
                            location=fa.get("location", ""),
                            severity=role,
                            layer=ValidationLayer.SCHEMATRON
                        ))
                        
            except Exception as e:
                logger.error(f"Saxon Execution Error: {e}")
                errors.append(ValidationError("SYS-SAXON", str(e), "", "error", ValidationLayer.SYSTEM))
                schematron_valid = False
                
        return ValidationResult(
            is_valid=xsd_valid and schematron_valid,
            xsd_valid=xsd_valid,
            schematron_valid=schematron_valid,
            errors=errors
        )


def validate_pdfa3(
    pdf_bytes: bytes, verapdf_jar: str
) -> Tuple[Optional[bool], List[ValidationError]]:
    """
    Validate PDF/A-3b compliance using VeraPDF via subprocess.

    Invokes VeraPDF as an isolated subprocess so the JVM is fully destroyed
    after each call — no memory leaks possible in the main Python process.

    Args:
        pdf_bytes: Raw PDF bytes to validate.
        verapdf_jar: Absolute path to the verapdf fat JAR.

    Returns:
        (pdfa_valid, errors) where pdfa_valid is True/False, or None on
        subprocess failure (so callers can distinguish "invalid" from "unknown").
    """
    try:
        with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as tmp:
            tmp.write(pdf_bytes)
            tmp_path = tmp.name

        try:
            proc = subprocess.run(
                [
                    "java",
                    "-Xms32m", "-Xmx256m",
                    "-jar", verapdf_jar,
                    "--flavour", "3b",   # PDF/A-3b — the Factur-X container profile
                    "--format", "mrr",   # Machine-Readable Report (XML)
                    tmp_path,
                ],
                capture_output=True,
                timeout=60,
            )

            if not proc.stdout:
                logger.warning(
                    "VeraPDF produced no stdout (stderr: %s)",
                    proc.stderr.decode(errors="replace")[:300],
                )
                return None, []

            try:
                mrr_doc = etree.fromstring(proc.stdout)
            except etree.XMLSyntaxError as parse_err:
                logger.error(
                    "VeraPDF MRR XML parse error: %s. Raw: %s",
                    parse_err,
                    proc.stdout[:300],
                )
                return None, [
                    ValidationError(
                        rule_id="PDFA-PARSE-ERROR",
                        message=f"VeraPDF output could not be parsed: {parse_err}",
                        location="",
                        severity="error",
                        layer=ValidationLayer.SYSTEM,
                    )
                ]

            ns = {"vp": VERAPDF_MRR_NS}
            vr = mrr_doc.find(".//vp:validationReport", ns)
            if vr is None:
                logger.warning("VeraPDF: validationReport element missing in MRR output")
                return None, []

            is_compliant = vr.get("isCompliant", "false").lower() == "true"
            errors: List[ValidationError] = []

            if not is_compliant:
                for rule in vr.findall(".//vp:rule[@status='failed']", ns):
                    clause = rule.get("clause", "")
                    test_num = rule.get("testNumber", "")
                    rule_id = f"PDFA-3B-{clause}.{test_num}".replace("/", "-")

                    desc_el = rule.find("vp:description", ns)
                    description = (
                        desc_el.text.strip()
                        if desc_el is not None and desc_el.text
                        else "PDF/A-3b compliance violation"
                    )

                    error_els = rule.findall("vp:error", ns)
                    if error_els:
                        for err_el in error_els:
                            err_msg = err_el.get("message", description)
                            loc_el = err_el.find("vp:location", ns)
                            location = (
                                loc_el.text.strip()
                                if loc_el is not None and loc_el.text
                                else clause
                            )
                            errors.append(
                                ValidationError(
                                    rule_id=rule_id,
                                    message=err_msg,
                                    location=location,
                                    severity="error",
                                    layer=ValidationLayer.PDF_A,
                                )
                            )
                    else:
                        errors.append(
                            ValidationError(
                                rule_id=rule_id,
                                message=description,
                                location=clause,
                                severity="error",
                                layer=ValidationLayer.PDF_A,
                            )
                        )

            return is_compliant, errors

        finally:
            os.unlink(tmp_path)

    except subprocess.TimeoutExpired:
        logger.error("VeraPDF validation timed out after 60s")
        return None, [
            ValidationError(
                rule_id="PDFA-TIMEOUT",
                message="VeraPDF PDF/A-3b validation timed out after 60 seconds",
                location="",
                severity="error",
                layer=ValidationLayer.SYSTEM,
            )
        ]
    except Exception as exc:
        logger.error("VeraPDF subprocess error: %s", exc)
        return None, [
            ValidationError(
                rule_id="PDFA-ERROR",
                message=f"VeraPDF validation failed: {exc}",
                location="",
                severity="error",
                layer=ValidationLayer.SYSTEM,
            )
        ]
