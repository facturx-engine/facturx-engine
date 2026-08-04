from pathlib import Path

from app.services.hybrid_validation_service import (
    EXTENDED_XSD_PATH,
    UBL_XSD_CREDITNOTE_PATH,
    UBL_XSD_INVOICE_PATH,
    HybridValidationService,
)

CORPUS_ROOT = Path(__file__).parent / "corpus"


def test_ubl_xsd_artifacts_are_available_and_applied():
    invoice = CORPUS_ROOT / "corpus-master" / "XML-Rechnung" / "UBL" / "EN16931_Einfach.ubl.xml"

    assert UBL_XSD_INVOICE_PATH.exists()
    assert UBL_XSD_CREDITNOTE_PATH.exists()

    result = HybridValidationService.validate(invoice.read_bytes(), invoice.name)

    assert result["format_detected"] == "ubl"
    assert result["xsd_valid"] is True
    assert "xsd" in result["layers_executed"]


def test_extended_xsd_is_applied():
    invoice = (
        CORPUS_ROOT
        / "ZUGFeRD-2.4-examples"
        / "_ZUGFeRD 2.4 examples"
        / "4. EXTENDED"
        / "EXTENDED_Fremdwaehrung"
        / "EXTENDED_Fremdwaehrung.xml"
    )

    assert EXTENDED_XSD_PATH.exists()

    result = HybridValidationService.validate(invoice.read_bytes(), invoice.name)

    assert result["profile_detected"] == "extended"
    assert result["xsd_valid"] is True
    assert "xsd" in result["layers_executed"]
