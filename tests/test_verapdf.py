"""
Tests for VeraPDF PDF/A-3b validation integration.

Tests that require the VeraPDF JAR are automatically skipped when
VERAPDF_JAR is not set (e.g. in CI without Java). Schema-level tests
run unconditionally.
"""
import os
import pytest
from pathlib import Path

VERAPDF_JAR = os.getenv("VERAPDF_JAR", "")
VERAPDF_AVAILABLE = bool(VERAPDF_JAR and os.path.exists(VERAPDF_JAR))

CORPUS_DIR = Path(__file__).parent / "corpus"


# ---------------------------------------------------------------------------
# Schema tests — no VeraPDF needed
# ---------------------------------------------------------------------------

def test_validation_result_has_pdfa_valid_field():
    """ValidationResult Pydantic model exposes pdfa_valid."""
    from app.schemas.validation import ValidationResult
    instance = ValidationResult(valid=True, errors=[])
    assert hasattr(instance, "pdfa_valid")
    assert instance.pdfa_valid is None


def test_pro_validation_result_has_pdfa_valid_field():
    """ProValidationResult Pydantic model exposes pdfa_valid."""
    from app.schemas.validation import ProValidationResult
    instance = ProValidationResult(valid=True, error_count=0)
    assert hasattr(instance, "pdfa_valid")
    assert instance.pdfa_valid is None


def test_service_result_includes_pdfa_valid_key_for_pdf():
    """HybridValidationService.validate() always returns pdfa_valid in its dict."""
    from app.services.hybrid_validation_service import HybridValidationService

    valid_pdfs = list((CORPUS_DIR / "valid").rglob("*.pdf"))
    if not valid_pdfs:
        pytest.skip("No valid PDF corpus files found")

    content = valid_pdfs[0].read_bytes()
    result = HybridValidationService.validate(content, valid_pdfs[0].name)

    assert "pdfa_valid" in result


def test_service_result_pdfa_valid_is_none_for_xml():
    """XML-only input must yield pdfa_valid=None (VeraPDF does not apply to XML)."""
    from app.services.hybrid_validation_service import HybridValidationService

    valid_xmls = list((CORPUS_DIR / "valid").rglob("*.xml"))
    if not valid_xmls:
        pytest.skip("No valid XML corpus files found")

    content = valid_xmls[0].read_bytes()
    result = HybridValidationService.validate(content, valid_xmls[0].name)

    assert result.get("pdfa_valid") is None, (
        "pdfa_valid should be None for raw XML input — VeraPDF only applies to PDFs"
    )


# ---------------------------------------------------------------------------
# VeraPDF subprocess tests — skipped when JAR not available
# ---------------------------------------------------------------------------

@pytest.mark.skipif(not VERAPDF_AVAILABLE, reason="VERAPDF_JAR not configured or not found")
def test_validate_pdfa3_valid_invoice():
    """A genuine Factur-X PDF must be PDF/A-3b compliant."""
    from app.services.hybrid_validator import validate_pdfa3

    valid_pdfs = list((CORPUS_DIR / "valid").rglob("*.pdf"))
    if not valid_pdfs:
        pytest.skip("No valid PDF corpus files found")

    pdf_bytes = valid_pdfs[0].read_bytes()
    pdfa_valid, errors = validate_pdfa3(pdf_bytes, VERAPDF_JAR)

    hard_errors = [e for e in errors if e.severity == "error" and e.rule_id != "PDFA-TIMEOUT"]
    assert pdfa_valid is True, (
        f"Expected {valid_pdfs[0].name} to be PDF/A-3b compliant. "
        f"Errors: {[e.message for e in hard_errors]}"
    )


@pytest.mark.skipif(not VERAPDF_AVAILABLE, reason="VERAPDF_JAR not configured or not found")
def test_validate_pdfa3_returns_errors_for_non_compliant():
    """A plain PDF (not PDF/A-3) must be reported as non-compliant."""
    from app.services.hybrid_validator import validate_pdfa3

    # bare_invoice.pdf is a plain PDF without Factur-X XML — also not PDF/A-3
    plain_pdf = CORPUS_DIR / "valid" / "bare_invoice.pdf"
    if not plain_pdf.exists():
        pytest.skip("bare_invoice.pdf not in corpus")

    pdf_bytes = plain_pdf.read_bytes()
    pdfa_valid, errors = validate_pdfa3(pdf_bytes, VERAPDF_JAR)

    assert pdfa_valid is False, "bare_invoice.pdf should fail PDF/A-3b validation"
    assert len(errors) > 0, "Expected at least one error for non-compliant PDF"
    assert all(e.layer.value == "pdf_a" for e in errors if e.rule_id != "PDFA-ERROR")


@pytest.mark.skipif(not VERAPDF_AVAILABLE, reason="VERAPDF_JAR not configured or not found")
def test_validate_pdfa3_errors_have_correct_layer():
    """VeraPDF errors must be tagged with layer=pdf_a."""
    from app.services.hybrid_validator import validate_pdfa3, ValidationLayer

    plain_pdf = CORPUS_DIR / "valid" / "bare_invoice.pdf"
    if not plain_pdf.exists():
        pytest.skip("bare_invoice.pdf not in corpus")

    _, errors = validate_pdfa3(plain_pdf.read_bytes(), VERAPDF_JAR)

    pdf_a_errors = [e for e in errors if e.layer == ValidationLayer.PDF_A]
    assert len(pdf_a_errors) > 0, "Expected errors with layer=pdf_a"


@pytest.mark.skipif(not VERAPDF_AVAILABLE, reason="VERAPDF_JAR not configured or not found")
def test_service_pdfa_valid_false_marks_document_invalid():
    """When VeraPDF finds errors, is_valid must be False in the service result."""
    from app.services.hybrid_validation_service import HybridValidationService

    plain_pdf = CORPUS_DIR / "valid" / "bare_invoice.pdf"
    if not plain_pdf.exists():
        pytest.skip("bare_invoice.pdf not in corpus")

    result = HybridValidationService.validate(plain_pdf.read_bytes(), "bare_invoice.pdf")

    if result.get("pdfa_valid") is False:
        assert result["is_valid"] is False, (
            "is_valid must be False when pdfa_valid is False"
        )
