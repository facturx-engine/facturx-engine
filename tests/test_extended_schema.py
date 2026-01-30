import json
import xml.etree.ElementTree as ET
from fastapi.testclient import TestClient
from reportlab.pdfgen import canvas
from io import BytesIO
import pytest

from app.main import app
from app.schemas.validation import InvoiceMetadata

client = TestClient(app)

def create_dummy_pdf():
    buffer = BytesIO()
    c = canvas.Canvas(buffer)
    c.drawString(100, 750, "Extended Invoice Template")
    c.save()
    return buffer.getvalue()

def test_extended_fields_roundtrip():
    """
    Test that all new extended fields are correctly:
    1. Accepted by the API
    2. Embedded in the XML
    3. Correctly placed in the XML (XSD ordering)
    4. Recoverable via extraction
    """
    metadata = {
        "invoice_number": "EXT-FIELD-ROUNDTRIP-001",
        "issue_date": "20260129",
        "seller": {
            "name": "Super Seller Corp",
            "id": "SELLER-ID-001",
            "address": {
                "line1": "123 Seller St",
                "postcode": "75001",
                "city": "Paris",
                "country_code": "FR"
            },
            "vat_number": "FR12345678901",
            "iban": "FR7612345678901234567890123",
            "bank_name": "Test Bank",
            "email": "contact@seller.com",
            "phone": "+33123456789"
        },
        "buyer": {
            "name": "Greedy Buyer Ltd",
            "id": "CUST-999",
            "address": {
                "line1": "456 Buyer Rd",
                "postcode": "69001",
                "city": "Lyon",
                "country_code": "FR"
            }
        },
        "ship_to": {
            "name": "Warehouse A",
            "id": "LOC-W-A",
            "address": {
                "line1": "789 Delivery Ave",
                "postcode": "13001",
                "city": "Marseille",
                "country_code": "FR"
            }
        },
        "delivery_date": "20260130",
        "buyer_reference": "REF-PO-456",
        "payment_terms": "Paiement à 30 jours",
        "lines": [
            {
                "line_id": "1",
                "name": "Consulting Services",
                "quantity": 1.0,
                "unit_code": "C62",
                "net_price": 100.0,
                "net_total": 100.0,
                "vat_rate": 20.0,
                "vat_category": "S"
            }
        ],
        "tax_details": [
            {
                "calculated_amount": "20.00",
                "basis_amount": "100.00",
                "rate": "20.00",
                "category_code": "S"
            }
        ],
        "amounts": {
            "tax_basis_total": "100.00",
            "tax_total": "20.00",
            "grand_total": "120.00",
            "due_payable": "120.00"
        },
        "currency_code": "EUR",
        "profile": "en16931"
    }
    
    # 1. Convert
    pdf_content = create_dummy_pdf()
    convert_response = client.post(
        "/v1/convert",
        files={"pdf": ("invoice.pdf", pdf_content, "application/pdf")},
        data={"metadata": json.dumps(metadata)}
    )
    
    assert convert_response.status_code == 200, f"Convert failed: {convert_response.text}"
    facturx_pdf = convert_response.content
    
    # 2. Extract and Verify XML tags directly
    extract_response = client.post(
        "/v1/extract",
        files={"file": ("facturx.pdf", facturx_pdf, "application/pdf")}
    )
    assert extract_response.status_code == 200
    
    # We also want to check the raw XML for specific tags
    # This is hidden in the validator's teaser or we can just extract it again
    from facturx import get_xml_from_pdf
    from io import BytesIO
    _, xml_content = get_xml_from_pdf(BytesIO(facturx_pdf))
    
    # Parse XML and check tags
    root = ET.fromstring(xml_content)
    namespaces = {
        'ram': 'urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100',
        'rsm': 'urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100',
        'udt': 'urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100'
    }
    
    # Check IBAN
    iban_element = root.find(".//ram:PayeePartyCreditorFinancialAccount/ram:IBANID", namespaces)
    assert iban_element is not None, "IBAN not found in XML"
    assert iban_element.text == metadata["seller"]["iban"]
    
    # Check IDs (Issue #5)
    seller_id = root.find(".//ram:SellerTradeParty/ram:ID", namespaces)
    assert seller_id is not None and seller_id.text == "SELLER-ID-001"
    
    buyer_id = root.find(".//ram:BuyerTradeParty/ram:ID", namespaces)
    assert buyer_id is not None and buyer_id.text == "CUST-999"
    
    shipto_id = root.find(".//ram:ShipToTradeParty/ram:ID", namespaces)
    assert shipto_id is not None and shipto_id.text == "LOC-W-A"
    
    # Check Phone/Email in Contact
    phone_element = root.find(".//ram:SellerTradeParty//ram:TelephoneUniversalCommunication/ram:CompleteNumber", namespaces)
    assert phone_element is not None, "Seller phone not found"
    assert phone_element.text == metadata["seller"]["phone"]
    
    # Check Delivery Name
    ship_to_name = root.find(".//ram:ApplicableHeaderTradeDelivery/ram:ShipToTradeParty/ram:Name", namespaces)
    assert ship_to_name is not None, "ShipTo name not found"
    assert ship_to_name.text == metadata["ship_to"]["name"]
    
    # Check Delivery Date
    delivery_date = root.find(".//ram:ApplicableHeaderTradeDelivery/ram:ActualDeliverySupplyChainEvent/ram:OccurrenceDateTime/udt:DateTimeString", namespaces)
    assert delivery_date is not None, "Delivery date not found"
    assert delivery_date.text == metadata["delivery_date"]

    # 3. Validate (using /v1/validate)
    validate_response = client.post(
        "/v1/validate",
        files={"file": ("facturx.pdf", facturx_pdf, "application/pdf")}
    )
    assert validate_response.status_code == 200
    validation_data = validate_response.json()
    assert validation_data["valid"] is True, f"Validation failed: {validation_data['errors']}"

def test_xml_endpoint():
    """Test the new /v1/xml endpoint for raw CII XML generation."""
    metadata = {
        "invoice_number": "XML-ONLY-001",
        "issue_date": "20260130",
        "seller": {"name": "Test Seller", "address": {"line1": "S1", "postcode": "1", "city": "C", "country_code": "FR"}},
        "buyer": {"name": "Test Buyer", "address": {"line1": "B1", "postcode": "2", "city": "C", "country_code": "FR"}},
        "lines": [{"line_id": "1", "name": "Item 1", "quantity": 1, "net_price": 10, "net_total": 10, "vat_rate": 20}],
        "tax_details": [{"calculated_amount": "2.00", "basis_amount": "10.00", "rate": "20.00"}],
        "amounts": {"tax_basis_total": "10.00", "tax_total": "2.00", "grand_total": "12.00", "due_payable": "12.00"},
        "profile": "en16931"
    }

    response = client.post(
        "/v1/xml",
        data={"metadata": json.dumps(metadata)}
    )

    assert response.status_code == 200
    assert response.headers["content-type"] == "application/xml"
    
    xml_content = response.content
    assert b"CrossIndustryInvoice" in xml_content
    assert b"XML-ONLY-001" in xml_content
    
    # Verify it's valid XML
    root = ET.fromstring(xml_content)
    assert root.tag.endswith("CrossIndustryInvoice")
