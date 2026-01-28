import os
import logging
from enum import Enum
from typing import List, Optional
from dataclasses import dataclass
from lxml import etree
from saxonche import PySaxonProcessor

logger = logging.getLogger(__name__)

class ValidationLayer(Enum):
    XSD = "xsd"
    SCHEMATRON = "schematron"
    SYSTEM = "system"

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
                # Security: Load XSD with strict parser
                schema_doc = etree.parse(self.xsd_path)
                schema = etree.XMLSchema(schema_doc)
                
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
                    input_node = proc.parse_xml(xml_text=xml_content.decode('utf-8'))
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
