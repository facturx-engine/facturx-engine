from app.services.generator import GeneratorService
from app.services.validator import ValidationService
from app.schemas.validation import InvoiceMetadata

metadata_dict = {
    "invoice_number": "SMOKE-001",
    "issue_date": "20260126",
    "seller": {
        "name": "Smoke Test Corp",
        "country_code": "FR",
        "vat_number": "FR999999999"
    },
    "buyer": {"name": "Test Client"},
    "lines": [
        {"name": "Test Item", "quantity": 1, "net_price": 100, "net_total": 100, "vat_rate": 20}
    ],
    "amounts": {
        "tax_basis_total": "100.00",
        "tax_total": "20.00",
        "grand_total": "120.00",
        "due_payable": "120.00"
    },
    "tax_details": [
        {"calculated_amount": "20.00", "basis_amount": "100.00", "rate": "20.00", "category_code": "S"}
    ],
    "currency_code": "EUR",
    "profile": "en16931"
}

try:
    print("Generating XML...")
    meta = InvoiceMetadata(**metadata_dict)
    xml = GeneratorService.generate_xml(meta)
    print(xml)
    
    xml_bytes = xml.encode('utf-8')
    is_valid, fmt, flavor, errors = ValidationService.validate_file(xml_bytes, "debug_smoke.xml")
    
    print(f"Valid: {is_valid}")
    print(f"Errors: {errors}")

except Exception as e:
    print(f"CRASH: {e}")
