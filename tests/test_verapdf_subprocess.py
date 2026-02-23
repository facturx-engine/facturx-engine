"""
Unit tests for the VeraPDF PDF/A-3b subprocess bridge (validate_pdfa3).

All subprocess calls are mocked — no Java runtime or VeraPDF JAR required.
Suitable for CI environments without a JVM.
"""
import subprocess
from unittest.mock import MagicMock, patch

from app.services.hybrid_validator import ValidationLayer, validate_pdfa3

FAKE_JAR = "/fake/verapdf.jar"
FAKE_PDF = b"%PDF-1.4 1 0 obj<</Type/Catalog>>endobj"

# -------------------------------------------------------------------------
# Minimal VeraPDF Machine-Readable Report (MRR) XML fixtures
# -------------------------------------------------------------------------

_MRR_COMPLIANT = b"""<?xml version="1.0" encoding="UTF-8"?>
<report xmlns="http://www.verapdf.org/MachineReadableReport">
  <validationReport flavour="3b" isCompliant="true" statement="compliant"/>
</report>"""

_MRR_NON_COMPLIANT = b"""<?xml version="1.0" encoding="UTF-8"?>
<report xmlns="http://www.verapdf.org/MachineReadableReport">
  <validationReport flavour="3b" isCompliant="false" statement="not compliant">
    <rule clause="6.1.2" testNumber="1" status="failed" passedChecks="0" failedChecks="1">
      <description>PDF version mismatch</description>
      <error message="Header version incorrect">
        <location>document root</location>
      </error>
    </rule>
  </validationReport>
</report>"""

_MRR_MISSING_REPORT = b"""<?xml version="1.0" encoding="UTF-8"?>
<report xmlns="http://www.verapdf.org/MachineReadableReport">
  <jobs/>
</report>"""


def _proc(stdout: bytes, returncode: int = 0) -> MagicMock:
    """Build a mock subprocess.CompletedProcess."""
    p = MagicMock()
    p.stdout = stdout
    p.stderr = b""
    p.returncode = returncode
    return p


# -------------------------------------------------------------------------
# Happy path: PDF/A-3b compliant document
# -------------------------------------------------------------------------

@patch("app.services.hybrid_validator.subprocess.run")
def test_compliant_pdf_returns_true_no_errors(mock_run):
    mock_run.return_value = _proc(_MRR_COMPLIANT)
    valid, errors = validate_pdfa3(FAKE_PDF, FAKE_JAR)

    assert valid is True
    assert errors == []


# -------------------------------------------------------------------------
# Non-compliant PDF: errors are extracted and tagged correctly
# -------------------------------------------------------------------------

@patch("app.services.hybrid_validator.subprocess.run")
def test_non_compliant_pdf_returns_false_with_errors(mock_run):
    mock_run.return_value = _proc(_MRR_NON_COMPLIANT)
    valid, errors = validate_pdfa3(FAKE_PDF, FAKE_JAR)

    assert valid is False
    assert len(errors) == 1
    assert errors[0].rule_id == "PDFA-3B-6.1.2.1"
    assert errors[0].layer == ValidationLayer.PDF_A
    assert errors[0].severity == "error"
    assert "Header version incorrect" in errors[0].message


# -------------------------------------------------------------------------
# Empty stdout: subprocess produced no output → (None, [])
# -------------------------------------------------------------------------

@patch("app.services.hybrid_validator.subprocess.run")
def test_empty_stdout_returns_none(mock_run):
    mock_run.return_value = _proc(b"")
    valid, errors = validate_pdfa3(FAKE_PDF, FAKE_JAR)

    assert valid is None
    assert errors == []


# -------------------------------------------------------------------------
# MRR XML missing validationReport element → (None, [])
# -------------------------------------------------------------------------

@patch("app.services.hybrid_validator.subprocess.run")
def test_missing_validation_report_element(mock_run):
    mock_run.return_value = _proc(_MRR_MISSING_REPORT)
    valid, errors = validate_pdfa3(FAKE_PDF, FAKE_JAR)

    assert valid is None
    assert errors == []


# -------------------------------------------------------------------------
# Malformed XML stdout → (None, [PDFA-PARSE-ERROR])
# -------------------------------------------------------------------------

@patch("app.services.hybrid_validator.subprocess.run")
def test_malformed_xml_stdout(mock_run):
    mock_run.return_value = _proc(b"<this >>> is not >>> xml")
    valid, errors = validate_pdfa3(FAKE_PDF, FAKE_JAR)

    assert valid is None
    assert len(errors) == 1
    assert errors[0].rule_id == "PDFA-PARSE-ERROR"
    assert errors[0].layer == ValidationLayer.SYSTEM


# -------------------------------------------------------------------------
# Timeout: subprocess.TimeoutExpired → (None, [PDFA-TIMEOUT])
# -------------------------------------------------------------------------

@patch("app.services.hybrid_validator.subprocess.run")
def test_timeout_returns_pdfa_timeout_error(mock_run):
    mock_run.side_effect = subprocess.TimeoutExpired(cmd=["java"], timeout=60)
    valid, errors = validate_pdfa3(FAKE_PDF, FAKE_JAR)

    assert valid is None
    assert len(errors) == 1
    assert errors[0].rule_id == "PDFA-TIMEOUT"
    assert errors[0].layer == ValidationLayer.SYSTEM


# -------------------------------------------------------------------------
# Generic OS/runtime error → (None, [PDFA-ERROR])
# -------------------------------------------------------------------------

@patch("app.services.hybrid_validator.subprocess.run")
def test_generic_exception_returns_pdfa_error(mock_run):
    mock_run.side_effect = OSError("java: No such file or directory")
    valid, errors = validate_pdfa3(FAKE_PDF, FAKE_JAR)

    assert valid is None
    assert len(errors) == 1
    assert errors[0].rule_id == "PDFA-ERROR"
    assert errors[0].layer == ValidationLayer.SYSTEM


# -------------------------------------------------------------------------
# Subprocess receives the correct VeraPDF CLI flags
# -------------------------------------------------------------------------

@patch("app.services.hybrid_validator.subprocess.run")
def test_subprocess_receives_correct_verapdf_flags(mock_run):
    mock_run.return_value = _proc(_MRR_COMPLIANT)
    validate_pdfa3(FAKE_PDF, FAKE_JAR)

    called_cmd = mock_run.call_args[0][0]
    assert called_cmd[0] == "java"
    assert "-jar" in called_cmd
    assert FAKE_JAR in called_cmd
    assert "--flavour" in called_cmd
    assert "3b" in called_cmd
    assert "--format" in called_cmd
    assert "mrr" in called_cmd
