
import pytest
from app.services.validator import ValidationService

def test_validator_rejects_corrupt_xml():
    # 1. Provide an XML that is syntactically valid but schema-invalid
    bad_xml = b"""<?xml version="1.0" encoding="UTF-8"?>
<rsm:CrossIndustryInvoice xmlns:rsm="urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100" 
                          xmlns:ram="urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100">
    <rsm:ExchangedDocument>
        <ram:ID>INV-ERROR</ram:ID>
        <!-- Missing required elements for Factur-X -->
    </rsm:ExchangedDocument>
</rsm:CrossIndustryInvoice>"""
    
    is_valid, format_type, flavor, errors = ValidationService.validate_file(bad_xml, "invalid.xml")
    
    print(f"Validation result: {is_valid}")
    print(f"Format: {format_type}")
    print(f"Errors: {errors}")
    
    assert is_valid is False
    assert len(errors) > 0
    # format_type can be None if XML is too corrupt to identify
    if format_type:
        assert "factur-x" in format_type
