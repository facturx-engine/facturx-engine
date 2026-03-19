from app.schemas.validation import (
    BuyerInfo,
    InvoiceMetadata,
    LineItem,
    MonetaryAmounts,
    SellerInfo,
)
from app.services.business_serializer import BusinessReadySerializer
from app.services.generator import GeneratorService


def test_xrechnung_30_roundtrip():
    """
    Verify that an XRechnung 3.0 invoice can be generated, 
    and then serialized back to JSON with all metadata (profile, references) preserved.
    """
    metadata = InvoiceMetadata(
        invoice_number="XR-2026-001",
        issue_date="20260219",
        profile="xrechnung_3.0",
        buyer_reference="BUYER-REF-123", # Mandatory for XRechnung
        seller=SellerInfo(
            name="Alpha Corp",
            address={"line1": "123 Tech St", "city": "Berlin", "postcode": "10115", "country_code": "DE"},
            vat_number="DE123456789"
        ),
        buyer=BuyerInfo(
            name="Beta Ltd",
            address={"line1": "456 Client Rd", "city": "Munich", "postcode": "80331", "country_code": "DE"}
        ),
        lines=[
            LineItem(name="Cloud Service", quantity=1.0, net_price=100.0, net_total=100.0, vat_rate=19.0)
        ],
        amounts=MonetaryAmounts(
            tax_basis_total="100.00",
            tax_total="19.00",
            grand_total="119.00",
            due_payable="119.00"
        )
    )

    # 1. Generate XML
    xml_str = GeneratorService.generate_xml(metadata)
    assert "urn:xeinkauf.de:kosit:xrechnung_3.0" in xml_str
    assert "<ram:BuyerReference>BUYER-REF-123</ram:BuyerReference>" in xml_str

    # 2. Serialize back to JSON
    invoice_json = BusinessReadySerializer.serialize(xml_str.encode('utf-8'))
    
    # Check Profile Persistence
    assert invoice_json.profile == "xrechnung_3.0"
    assert invoice_json.format == "factur-x"
    
    # Check Reference Persistence (Serializer)
    assert invoice_json.buyer_reference == "BUYER-REF-123"
    assert invoice_json.invoice_number == "XR-2026-001"
    
    # 3. Verify Extractor (Community) parity
    from app.services.extractor import ExtractionService
    extract_res = ExtractionService.extract_invoice_data(xml_str.encode('utf-8'), "test_xr.xml")
    inv_ext = extract_res.get("invoice_json", {})
    assert inv_ext.get("buyer_reference") == "BUYER-REF-123"
    assert inv_ext.get("contract_reference") is None # None in this test case

def test_zugferd_en16931_parity():
    """Verify parity for ZUGFeRD / Factur-X EN 16931 profile."""
    metadata = InvoiceMetadata(
        invoice_number="FX-PARITY-001",
        issue_date="20260219",
        profile="en16931",
        buyer_reference="PARITY-REF",
        contract_reference="CONTRACT-XYZ",
        seller=SellerInfo(name="S", address={"line1": "A", "city": "C", "postcode": "1", "country_code": "FR"}),
        buyer=BuyerInfo(name="B"),
        lines=[LineItem(name="I", quantity=1.0, net_price=10.0, net_total=10.0, vat_rate=20.0)],
        amounts=MonetaryAmounts(tax_basis_total="10.00", tax_total="2.00", grand_total="12.00", due_payable="12.00")
    )
    xml_str = GeneratorService.generate_xml(metadata)
    
    # 1. Serializer Pro
    inv_pro = BusinessReadySerializer.serialize(xml_str.encode('utf-8'))
    assert inv_pro.buyer_reference == "PARITY-REF"
    assert inv_pro.contract_reference == "CONTRACT-XYZ"
    
    # 2. Extractor Community
    from app.services.extractor import ExtractionService
    res_ext = ExtractionService.extract_invoice_data(xml_str.encode('utf-8'), "parity.xml")
    inv_ext = res_ext.get("invoice_json", {})
    assert inv_ext.get("buyer_reference") == "PARITY-REF"
    assert inv_ext.get("contract_reference") == "CONTRACT-XYZ"

def test_audit_fixes_regression_prevention():
    """Ensure older profiles still work correctly."""
    metadata = InvoiceMetadata(
        invoice_number="FX-2026-001",
        issue_date="20260219",
        profile="en16931",
        seller=SellerInfo(name="S", address={"line1": "A", "city": "C", "postcode": "1", "country_code": "FR"}),
        buyer=BuyerInfo(name="B"),
        lines=[LineItem(name="I", quantity=1.0, net_price=10.0, net_total=10.0, vat_rate=20.0)],
        amounts=MonetaryAmounts(tax_basis_total="10.00", tax_total="2.00", grand_total="12.00", due_payable="12.00")
    )
    xml_str = GeneratorService.generate_xml(metadata)
    assert "urn:cen.eu:en16931:2017" in xml_str
    
    invoice_json = BusinessReadySerializer.serialize(xml_str.encode('utf-8'))
    assert invoice_json.profile == "en16931"
