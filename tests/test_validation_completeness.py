"""
Tests for validation_completeness, layers_executed, and layers_skipped fields.

Verifies that the API response correctly reports which validation layers
actually ran vs. which were skipped (and why).
"""
import os
import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app

# Minimal valid CII EN16931 XML for testing (no PDF wrapper needed)
MINIMAL_CII_XML = b"""<?xml version="1.0" encoding="UTF-8"?>
<rsm:CrossIndustryInvoice
    xmlns:rsm="urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100"
    xmlns:ram="urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100"
    xmlns:qdt="urn:un:unece:uncefact:data:standard:QualifiedDataType:100"
    xmlns:udt="urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100">
  <rsm:ExchangedDocumentContext>
    <ram:GuidelineSpecifiedDocumentContextParameter>
      <ram:ID>urn:cen.eu:en16931:2017</ram:ID>
    </ram:GuidelineSpecifiedDocumentContextParameter>
  </rsm:ExchangedDocumentContext>
  <rsm:ExchangedDocument>
    <ram:ID>TEST-001</ram:ID>
    <ram:TypeCode>380</ram:TypeCode>
    <ram:IssueDateTime><udt:DateTimeString format="102">20260101</udt:DateTimeString></ram:IssueDateTime>
  </rsm:ExchangedDocument>
  <rsm:SupplyChainTradeTransaction>
    <ram:ApplicableHeaderTradeAgreement>
      <ram:SellerTradeParty>
        <ram:Name>Test Seller</ram:Name>
        <ram:PostalTradeAddress><ram:CountryID>DE</ram:CountryID></ram:PostalTradeAddress>
        <ram:SpecifiedTaxRegistration><ram:ID schemeID="VA">DE123456789</ram:ID></ram:SpecifiedTaxRegistration>
      </ram:SellerTradeParty>
      <ram:BuyerTradeParty>
        <ram:Name>Test Buyer</ram:Name>
        <ram:PostalTradeAddress><ram:CountryID>DE</ram:CountryID></ram:PostalTradeAddress>
      </ram:BuyerTradeParty>
    </ram:ApplicableHeaderTradeAgreement>
    <ram:ApplicableHeaderTradeDelivery/>
    <ram:ApplicableHeaderTradeSettlement>
      <ram:InvoiceCurrencyCode>EUR</ram:InvoiceCurrencyCode>
      <ram:ApplicableTradeTax>
        <ram:CalculatedAmount>19.00</ram:CalculatedAmount>
        <ram:TypeCode>VAT</ram:TypeCode>
        <ram:BasisAmount>100.00</ram:BasisAmount>
        <ram:CategoryCode>S</ram:CategoryCode>
        <ram:RateApplicablePercent>19.00</ram:RateApplicablePercent>
      </ram:ApplicableTradeTax>
      <ram:SpecifiedTradeSettlementHeaderMonetarySummation>
        <ram:LineTotalAmount>100.00</ram:LineTotalAmount>
        <ram:TaxBasisTotalAmount>100.00</ram:TaxBasisTotalAmount>
        <ram:TaxTotalAmount currencyID="EUR">19.00</ram:TaxTotalAmount>
        <ram:GrandTotalAmount>119.00</ram:GrandTotalAmount>
        <ram:DuePayableAmount>119.00</ram:DuePayableAmount>
      </ram:SpecifiedTradeSettlementHeaderMonetarySummation>
    </ram:ApplicableHeaderTradeSettlement>
    <ram:IncludedSupplyChainTradeLineItem>
      <ram:AssociatedDocumentLineDocument><ram:LineID>1</ram:LineID></ram:AssociatedDocumentLineDocument>
      <ram:SpecifiedTradeProduct><ram:Name>Widget</ram:Name></ram:SpecifiedTradeProduct>
      <ram:SpecifiedLineTradeAgreement>
        <ram:NetPriceProductTradePrice><ram:ChargeAmount>100.00</ram:ChargeAmount></ram:NetPriceProductTradePrice>
      </ram:SpecifiedLineTradeAgreement>
      <ram:SpecifiedLineTradeDelivery>
        <ram:BilledQuantity unitCode="C62">1</ram:BilledQuantity>
      </ram:SpecifiedLineTradeDelivery>
      <ram:SpecifiedLineTradeSettlement>
        <ram:ApplicableTradeTax><ram:TypeCode>VAT</ram:TypeCode><ram:CategoryCode>S</ram:CategoryCode><ram:RateApplicablePercent>19.00</ram:RateApplicablePercent></ram:ApplicableTradeTax>
        <ram:SpecifiedTradeSettlementLineMonetarySummation><ram:LineTotalAmount>100.00</ram:LineTotalAmount></ram:SpecifiedTradeSettlementLineMonetarySummation>
      </ram:SpecifiedLineTradeSettlement>
    </ram:IncludedSupplyChainTradeLineItem>
  </rsm:SupplyChainTradeTransaction>
</rsm:CrossIndustryInvoice>"""


class TestValidationCompleteness(unittest.TestCase):

    def setUp(self):
        self.client = TestClient(app)

    def test_partial_when_saxon_missing(self):
        """When SAXON_JAR is empty, Schematron is skipped → validation_completeness=partial."""
        with patch.dict(os.environ, {"LICENSE_KEY": "", "SAXON_JAR": ""}):
            with patch("app.license.is_licensed", return_value=False):
                with patch("app.services.hybrid_validation_service.SAXON_JAR", ""):
                    files = {"file": ("test.xml", MINIMAL_CII_XML, "application/xml")}
                    response = self.client.post("/v1/validate", files=files)
                    data = response.json()

                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(data["validation_completeness"], "partial")
                    self.assertIn("xsd", data["layers_executed"])

                    skipped_layers = [s["layer"] for s in data["layers_skipped"]]
                    self.assertIn("schematron", skipped_layers)

                    # Find the schematron skip reason
                    schematron_skip = next(s for s in data["layers_skipped"] if s["layer"] == "schematron")
                    self.assertIn("saxon_jar", schematron_skip["reason"])

    def test_full_when_all_layers_present(self):
        """When XSD and Saxon+XSLT are all available, validation_completeness=full (XML input, no PDF/A)."""
        fake_saxon = os.path.abspath(__file__)  # Use this test file as a fake JAR path (exists on disk)
        with patch.dict(os.environ, {"LICENSE_KEY": "", "SAXON_JAR": fake_saxon}):
            with patch("app.license.is_licensed", return_value=False):
                with patch("app.services.hybrid_validation_service.SAXON_JAR", fake_saxon):
                    # Mock Saxon subprocess to return clean SVRL (no failed-asserts)
                    import subprocess
                    clean_svrl = b"""<?xml version="1.0" encoding="UTF-8"?>
                    <svrl:schematron-output xmlns:svrl="http://purl.oclc.org/dsdl/svrl">
                    </svrl:schematron-output>"""
                    mock_proc = subprocess.CompletedProcess(args=[], returncode=0, stdout=clean_svrl, stderr=b"")
                    with patch("subprocess.run", return_value=mock_proc):
                        files = {"file": ("test.xml", MINIMAL_CII_XML, "application/xml")}
                        response = self.client.post("/v1/validate", files=files)
                        data = response.json()

                        self.assertEqual(response.status_code, 200)
                        self.assertEqual(data["validation_completeness"], "full")
                        self.assertIn("xsd", data["layers_executed"])
                        self.assertIn("schematron", data["layers_executed"])
                        self.assertEqual(data["layers_skipped"], [])

    def test_response_always_contains_completeness_fields(self):
        """Every validation response must include the 3 new fields, even for simple cases."""
        with patch.dict(os.environ, {"LICENSE_KEY": ""}):
            with patch("app.license.is_licensed", return_value=False):
                files = {"file": ("test.xml", MINIMAL_CII_XML, "application/xml")}
                response = self.client.post("/v1/validate", files=files)
                data = response.json()

                self.assertEqual(response.status_code, 200)
                self.assertIn("validation_completeness", data)
                self.assertIn("layers_executed", data)
                self.assertIn("layers_skipped", data)
                self.assertIsInstance(data["layers_executed"], list)
                self.assertIsInstance(data["layers_skipped"], list)
                self.assertIn(data["validation_completeness"], ("full", "partial"))


if __name__ == "__main__":
    unittest.main()
