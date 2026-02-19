import pytest
from lxml import etree
from app.services.hybrid_validation_service import HybridValidationService
from app.services.validation_utils import detect_format

def test_xrechnung_30_detection():
    """Test that XRechnung 3.0.x URN is correctly detected."""
    xml_content = b"""<?xml version="1.0" encoding="UTF-8"?>
<rsm:CrossIndustryInvoice xmlns:rsm="urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100"
                           xmlns:ram="urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100">
    <rsm:ExchangedDocumentContext>
        <ram:GuidelineSpecifiedDocumentContextParameter>
            <ram:ID>urn:xeinkauf.de:kosit:xrechnung_3.0</ram:ID>
        </ram:GuidelineSpecifiedDocumentContextParameter>
    </rsm:ExchangedDocumentContext>
</rsm:CrossIndustryInvoice>"""
    
    root = etree.fromstring(xml_content)
    format_type, profile = detect_format(root)
    
    assert format_type == "factur-x"
    assert profile == "xrechnung_3.0"

def test_xrechnung_30_validation_path_selection():
    """
    Test that XRechnung 3.0 profile triggers the correct schema selection.
    We don't necessarily need to run the full validation (SaxonC might be slow/missing in test),
    but we can mock the validator to check if paths are correct.
    """
    # This is more of an integration test. 
    # Since we want to verify the logic in HybridValidationService.validate
    
    xml_content = b"""<?xml version="1.0" encoding="UTF-8"?>
<rsm:CrossIndustryInvoice xmlns:rsm="urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100"
                           xmlns:ram="urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100"
                           xmlns:udt="urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100">
    <rsm:ExchangedDocumentContext>
        <ram:GuidelineSpecifiedDocumentContextParameter>
            <ram:ID>urn:xeinkauf.de:kosit:xrechnung_3.0</ram:ID>
        </ram:GuidelineSpecifiedDocumentContextParameter>
    </rsm:ExchangedDocumentContext>
    <rsm:ExchangedDocument>
        <ram:ID>INV-123</ram:ID>
        <ram:TypeCode>380</ram:TypeCode>
        <ram:IssueDateTime>
            <udt:DateTimeString format="102">20260219</udt:DateTimeString>
        </ram:IssueDateTime>
    </rsm:ExchangedDocument>
</rsm:CrossIndustryInvoice>"""

    # We can check if the paths exist
    from app.services.hybrid_validation_service import XRECHNUNG_30_XSD, XRECHNUNG_30_XSLT
    
    assert XRECHNUNG_30_XSD.exists(), f"XRechnung 3.0 XSD not found at {XRECHNUNG_30_XSD}"
    assert XRECHNUNG_30_XSLT.exists(), f"XRechnung 3.0 XSLT not found at {XRECHNUNG_30_XSLT}"

    # Actually call validate (wait, this might fail if the XML is too minimal for the XSD)
    # But it proves the service can run with these files.
    result = HybridValidationService.validate(xml_content, "xrechnung.xml")
    
    # Even if it's invalid (due to missing fields), it should NOT be FX-INTERNAL or FX-POOL-ERROR 
    # which would indicate missing schemas or crashing SaxonC.
    # It should have errors from the new XSD/Schematron.
    assert "FX-INTERNAL" not in [e["rule_id"] for e in result["errors"]]
    assert result["profile_detected"] == "xrechnung_3.0"
