from app.services.generator import GeneratorService
from app.services.validator import ValidationService
from app.schemas.validation import InvoiceMetadata, SellerInfo, BuyerInfo, MonetaryAmounts

metadata_dict = {
    "invoice_number": "E2E-EXTRACT-001",
    "issue_date": "20260113",
    "seller": {
        "name": "Test Seller Corp",
        "country_code": "FR",
        "vat_number": "FR98765432101"
    },
    "buyer": {
        "name": "Test Buyer Ltd"
    },
    "amounts": {
        "tax_basis_total": "500.00",
        "tax_total": "100.00",
        "grand_total": "600.00",
        "due_payable": "600.00"
    },
    "currency_code": "EUR",
    "profile": "minimum"
}

try:
    meta = InvoiceMetadata(**metadata_dict)
    xml = GeneratorService.generate_xml(meta)
    xml_bytes = xml.encode('utf-8')
    
    is_valid, fmt, flavor, errors = ValidationService.validate_file(xml_bytes, "debug.xml")
    
    print(f"Valid: {is_valid}")
    print(f"Errors: {errors}")
except Exception as e:
    print(f"CRASH: {e}")
