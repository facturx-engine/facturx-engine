
import pytest
from app.services.validator import ValidationService
from app.services.generator import GeneratorService
from app.schemas.validation import InvoiceMetadata, SellerInfo, BuyerInfo, MonetaryAmounts

def get_valid_xml_base():
    metadata = InvoiceMetadata(
        invoice_number="INV-2024-001",
        issue_date="20240101",
        seller=SellerInfo(name="Seller Corp", country_code="FR", vat_number="FR123"),
        buyer=BuyerInfo(name="Buyer Ltd"),
        amounts=MonetaryAmounts(
            tax_basis_total="100.00",
            tax_total="20.00",
            grand_total="120.00",
            due_payable="120.00"
        ),
        currency_code="EUR",
        profile="minimum"
    )
    return GeneratorService.generate_xml(metadata).encode('utf-8')

def test_human_error_missing_typecode():
    valid_xml = get_valid_xml_base().decode('utf-8')
    # Delete <ram:TypeCode>380</ram:TypeCode>
    import re
    bad_xml_str = re.sub(r'<ram:TypeCode>.*?</ram:TypeCode>', '', valid_xml)
    bad_xml = bad_xml_str.encode('utf-8')
    
    is_valid, fmt, flavor, errors = ValidationService.validate_file(bad_xml, "test.xml")
    
    print(f"Validation result: {is_valid}")
    print(f"Errors found: {errors}")
    assert is_valid is False
    assert any("type de document" in err.lower() for err in errors)

def test_validator_sensitivity_nuclear():
    # Pass a completely invalid XML
    bad_xml = b"<root>Not an invoice</root>"
    
    is_valid, fmt, flavor, errors = ValidationService.validate_file(bad_xml, "test.xml")
    
    print(f"\n--- NUCLEAR TEST ---")
    print(f"Validation result: {is_valid}")
    print(f"Errors found: {errors}")
    assert is_valid is False
    assert len(errors) > 0
