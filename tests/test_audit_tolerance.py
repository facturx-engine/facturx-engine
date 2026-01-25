from app.services.generator import GeneratorService
from app.services.validator import ValidationService
from app.schemas.validation import InvoiceMetadata, SellerInfo, BuyerInfo, MonetaryAmounts, LineItem

def test_strict_tolerance_rejection():
    # 1. Create metadata for EN16931 (which triggers Schematron)
    # 2. Introduce a 0.05 error (Previous tolerance 0.10 allowed it, New 0.01 should BLOCK it)
    
    metadata = InvoiceMetadata(
        invoice_number="AUDIT-TOLERANCE-001",
        issue_date="20260126",
        seller=SellerInfo(
            name="Strict Seller", 
            address={"line1": "Rue de la Loi", "postcode": "75000", "city": "Paris", "country_code": "FR"},
            siret="12345678900010"
        ),
        buyer=BuyerInfo(name="Strict Buyer"),
        lines=[
            LineItem(
                name="Item 1",
                quantity=1.0,
                net_price=100.00,
                net_total=100.00,
                vat_rate=20.00,
                vat_category="S"
            )
        ],
        tax_details=[
             {"calculated_amount": "20.00", "basis_amount": "100.00", "rate": "20.00", "category_code": "S"}
        ],
        amounts=MonetaryAmounts(
            tax_basis_total="100.00", # Real
            tax_total="20.00",        # Real
            grand_total="120.05",     # ERROR: Should be 120.00. Diff is 0.05.
            due_payable="120.05"
        ),
        currency_code="EUR",
        profile="en16931"
    )
    
    xml = GeneratorService.generate_xml(metadata)
    xml_bytes = xml.encode('utf-8')
    
    is_valid, fmt, flavor, errors = ValidationService.validate_file(xml_bytes, "audit.xml")
    
    print(f"Valid: {is_valid}")
    print(f"Errors: {errors}")
    
    # Assert INVALID
    assert is_valid is False
    
    # Assert ERROR is BR-CO-16 (VAT) or similar
    assert any("BR-CO-16" in e or "incoherent" in e for e in errors)

if __name__ == "__main__":
    test_strict_tolerance_rejection()
    print("SUCCESS: 0.05 Error was Rejected")
