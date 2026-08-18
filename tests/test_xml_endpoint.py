"""
Tests for the /v1/xml endpoint — raw XML generation without PDF wrapper.
"""
import json

import pytest
from fastapi.testclient import TestClient
from lxml import etree

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


def valid_metadata():
    """Return minimal valid invoice metadata for XML generation."""
    return {
        "invoice_number": "XML-TEST-001",
        "issue_date": "20260217",
        "seller": {
            "name": "XML Test Seller",
            "address": {
                "line1": "1 Test Street",
                "postcode": "75001",
                "city": "Paris",
                "country_code": "FR"
            },
            "vat_number": "FR12345678901"
        },
        "buyer": {
            "name": "XML Test Buyer",
            "address": {
                "line1": "2 Buyer Road",
                "postcode": "69001",
                "city": "Lyon",
                "country_code": "FR"
            }
        },
        "lines": [
            {
                "line_id": "1",
                "name": "Consulting Service",
                "quantity": 2.0,
                "net_price": 250.0,
                "net_total": 500.0,
                "vat_rate": 20.0,
                "vat_category": "S"
            }
        ],
        "tax_details": [
            {
                "calculated_amount": "100.00",
                "basis_amount": "500.00",
                "rate": "20.00",
                "category_code": "S"
            }
        ],
        "amounts": {
            "tax_basis_total": "500.00",
            "tax_total": "100.00",
            "grand_total": "600.00",
            "due_payable": "600.00"
        },
        "currency_code": "EUR",
        "profile": "en16931",
        "payment_terms": "Net 30 days"
    }


def test_xml_generation_success(client):
    """Test that /v1/xml returns valid CII XML for valid metadata."""
    metadata = valid_metadata()

    response = client.post(
        "/v1/xml",
        data={"metadata": json.dumps(metadata)}
    )

    assert response.status_code == 200
    assert response.headers["content-type"].startswith("application/xml")

    # Verify it's actual XML
    content = response.content.decode("utf-8")
    assert content.startswith("<?xml") or content.startswith("<rsm:")
    assert "CrossIndustryInvoice" in content
    assert "XML-TEST-001" in content


def test_xml_generation_has_correct_filename(client):
    """Test that the Content-Disposition header uses the invoice number."""
    metadata = valid_metadata()

    response = client.post(
        "/v1/xml",
        data={"metadata": json.dumps(metadata)}
    )

    assert response.status_code == 200
    disposition = response.headers.get("content-disposition", "")
    assert "facturx_XML-TEST-001.xml" in disposition


def test_xml_generation_invalid_json(client):
    """Test that /v1/xml returns 400 for malformed JSON."""
    response = client.post(
        "/v1/xml",
        data={"metadata": "{not valid json}"}
    )

    assert response.status_code == 400
    data = response.json()
    assert data["type"] == "urn:facturx:error:invalid_json"


def test_xml_generation_missing_fields(client):
    """Test that /v1/xml returns 400 when required fields are missing."""
    incomplete = {"invoice_number": "INCOMPLETE-001"}

    response = client.post(
        "/v1/xml",
        data={"metadata": json.dumps(incomplete)}
    )

    assert response.status_code == 400
    data = response.json()
    assert data["type"] == "urn:facturx:error:invalid_metadata"


def test_xml_generation_rejects_missing_tax_breakdown(client):
    """Line-level profiles must not manufacture a tax breakdown."""
    metadata = valid_metadata()
    metadata["tax_details"] = []

    response = client.post(
        "/v1/xml",
        data={"metadata": json.dumps(metadata)},
    )

    assert response.status_code == 400
    assert response.json()["type"] == "urn:facturx:error:invalid_metadata"


def test_xml_generation_does_not_invent_delivery_date(client):
    metadata = valid_metadata()

    response = client.post(
        "/v1/xml",
        data={"metadata": json.dumps(metadata)},
    )

    assert response.status_code == 200
    assert "ActualDeliverySupplyChainEvent" not in response.text


def test_xml_generation_preserves_document_level_en16931_fields(client):
    metadata = valid_metadata()
    metadata["tax_details"][0]["exemption_reason"] = "Reverse charge"
    metadata["billing_period"] = {"start": "20260701", "end": "20260731"}
    metadata["purchase_order_reference"] = "BC-1234"
    metadata["preceding_invoices"] = [
        {"reference": "FA-2026-0042", "issue_date": "20260715"}
    ]
    metadata["tax_accounting_currency_code"] = "GBP"
    metadata["tax_accounting_currency_amount"] = "85.00"

    response = client.post("/v1/xml", data={"metadata": json.dumps(metadata)})

    assert response.status_code == 200
    root = etree.fromstring(response.content)
    ns = {
        "ram": "urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100",
        "qdt": "urn:un:unece:uncefact:data:standard:QualifiedDataType:100",
    }
    assert root.xpath("string(//ram:ApplicableTradeTax/ram:ExemptionReason)", namespaces=ns) == "Reverse charge"
    assert root.xpath("string(//ram:BillingSpecifiedPeriod/ram:StartDateTime/*)", namespaces=ns) == "20260701"
    assert root.xpath("string(//ram:BillingSpecifiedPeriod/ram:EndDateTime/*)", namespaces=ns) == "20260731"
    assert root.xpath("string(//ram:BuyerOrderReferencedDocument/ram:IssuerAssignedID)", namespaces=ns) == "BC-1234"
    assert root.xpath("string(//ram:InvoiceReferencedDocument/ram:IssuerAssignedID)", namespaces=ns) == "FA-2026-0042"
    assert root.xpath("string(//ram:InvoiceReferencedDocument/ram:FormattedIssueDateTime/qdt:DateTimeString)", namespaces=ns) == "20260715"
    assert root.xpath("string(//ram:TaxCurrencyCode)", namespaces=ns) == "GBP"
    tax_totals = root.xpath("//ram:TaxTotalAmount", namespaces=ns)
    assert [(node.get("currencyID"), node.text) for node in tax_totals] == [
        ("EUR", "100.00"),
        ("GBP", "85.00"),
    ]


def test_xml_generation_rejects_incomplete_tax_accounting_currency_pair(client):
    metadata = valid_metadata()
    metadata["tax_accounting_currency_code"] = "GBP"

    response = client.post("/v1/xml", data={"metadata": json.dumps(metadata)})

    assert response.status_code == 400
    assert "must be provided together" in response.text


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
