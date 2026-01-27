"""
Tests for the /v1/extract endpoint and end-to-end flow.
"""
import pytest
from fastapi.testclient import TestClient
import json
from io import BytesIO
from reportlab.pdfgen import canvas

from app.main import app

client = TestClient(app)


def create_dummy_pdf() -> bytes:
    """Create a simple dummy PDF for testing."""
    buffer = BytesIO()
    pdf = canvas.Canvas(buffer)
    pdf.drawString(100, 750, "Test Invoice")
    pdf.showPage()
    pdf.save()
    buffer.seek(0)
    return buffer.read()


def test_extract_non_facturx_pdf():
    """Test extraction from a PDF without Factur-X XML."""
    pdf_content = create_dummy_pdf()
    
    response = client.post(
        "/v1/extract",
        files={"file": ("test.pdf", pdf_content, "application/pdf")}
    )
    
    assert response.status_code == 200
    data = response.json()
    
    # Should detect as not_facturx
    assert data["format_detected"] == "not_facturx"
    assert data["xml_extracted"] is False
    assert any("NO_XML" in error["code"] for error in data["errors"])


def test_end_to_end_convert_validate_extract():
    """
    Full product workflow test:
    1. Convert PDF → Factur-X
    2. Validate the result
    3. Extract and parse the data
    """
    # Step 1: Convert
    pdf_content = create_dummy_pdf()
    
    metadata = {
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
    
    convert_response = client.post(
        "/v1/convert",
        files={"pdf": ("invoice.pdf", pdf_content, "application/pdf")},
        data={"metadata": json.dumps(metadata)}
    )
    
    assert convert_response.status_code == 200
    facturx_pdf = convert_response.content
    assert len(facturx_pdf) > 0
    
    # Step 2: Validate
    validate_response = client.post(
        "/v1/validate",
        files={"file": ("facturx.pdf", facturx_pdf, "application/pdf")}
    )
    
    assert validate_response.status_code == 200
    validation_data = validate_response.json()
    assert validation_data["valid"] is True
    assert validation_data["format"] == "factur-x"
    assert validation_data["flavor"] == "minimum"
    
    # Step 3: Extract
    extract_response = client.post(
        "/v1/extract",
        files={"file": ("facturx.pdf", facturx_pdf, "application/pdf")}
    )
    
    print(f"\nDEBUG_EXTRACT_STATUS: {extract_response.status_code}")
    if extract_response.status_code != 200:
        print(f"DEBUG_EXTRACT_FAIL_BODY: {extract_response.text}")
    
    # Try to parse anyway
    try:
        extract_data = extract_response.json()
        print(f"\nDEBUG_EXTRACT_DATA: {json.dumps(extract_data, indent=2)}")
    except:
        print("Could not parse JSON response")
        
    assert extract_response.status_code == 200
    
    # Verify extraction succeeded
    assert extract_data["format_detected"] == "factur-x"
    assert extract_data["profile_detected"] == "minimum"
    assert extract_data["xml_extracted"] is True
    assert len(extract_data["errors"]) == 0
    
    # Verify invoice data was parsed correctly
    invoice_json = extract_data["invoice_json"]
    print(f"\nDEBUG_INVOICE_JSON: {json.dumps(invoice_json, indent=2)}")
    assert invoice_json is not None
    assert invoice_json["invoice_number"] == "E2E-EXTRACT-001"
    assert invoice_json["invoice_date"] == "20260113"
    assert invoice_json["currency"] == "EUR"
    
    # Verify seller data
    # Verify seller data (Demo Mode masks it)
    # Pro would be "Test Seller Corp", Demo is "Test ****"
    assert "Test" in invoice_json["seller"]["name"] 
    assert "****" in invoice_json["seller"]["name"]
    # assert invoice_json["seller"]["country"] == "FR" if "country" in invoice_json["seller"] else True
    # VAT is masked to DEMO_***** in v1.3.1
    assert invoice_json["seller"]["vat_number"] == "DEMO_*****"
    
    # Verify buyer data
    assert "Test" in invoice_json["buyer"]["name"]
    
    # Verify totals (Real Values extracted in v1.3.1)
    assert invoice_json["totals"]["net_amount"] == "500.00"
    assert invoice_json["totals"]["tax_amount"] == "100.00"
    assert invoice_json["totals"]["gross_amount"] == "600.00"
    assert invoice_json["totals"]["payable_amount"] == "600.00"
    
    print("\n✓ END-TO-END TEST PASSED:")
    print("  - Convert: PDF → Factur-X PDF")
    print("  - Validate: EN 16931 compliance")
    print("  - Extract: Structured JSON data")
    print("  → Full product workflow validated!")


def test_diagnostics_endpoint():
    """Test the /diagnostics endpoint."""
    response = client.get("/diagnostics")
    assert response.status_code == 200
    
    data = response.json()
    
    # Verify version info
    assert "version" in data
    assert "git_hash" in data
    assert "build_date" in data
    
    # Verify runtime config
    assert "runtime_config" in data
    assert "environment" in data
    assert "memory_status" in data
    
    # Verify features
    assert "features_enabled" in data
    features = data["features_enabled"]
    assert "validate" in features
    assert "convert" in features
    assert "extract" in features
    
    # Should have either community or paid mode
    assert any("mode:" in f for f in features)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
