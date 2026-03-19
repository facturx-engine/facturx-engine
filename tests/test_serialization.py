import json
import os
import unittest
from pathlib import Path
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.services.business_serializer import BusinessReadySerializer


class TestSerialization(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)

    @staticmethod
    def _rich_cii_xml() -> bytes:
        return b'''<?xml version="1.0" encoding="UTF-8"?>
<rsm:CrossIndustryInvoice xmlns:rsm="urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100"
 xmlns:ram="urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100"
 xmlns:udt="urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100">
  <rsm:ExchangedDocumentContext>
    <ram:GuidelineSpecifiedDocumentContextParameter>
      <ram:ID>urn:cen.eu:en16931:2017</ram:ID>
    </ram:GuidelineSpecifiedDocumentContextParameter>
  </rsm:ExchangedDocumentContext>
  <rsm:ExchangedDocument>
    <ram:ID>INV-OK-001</ram:ID>
    <ram:IssueDateTime><udt:DateTimeString format="102">20260101</udt:DateTimeString></ram:IssueDateTime>
  </rsm:ExchangedDocument>
  <rsm:SupplyChainTradeTransaction>
    <ram:ApplicableHeaderTradeAgreement>
      <ram:SellerTradeParty>
        <ram:Name>Seller Corp</ram:Name>
        <ram:PostalTradeAddress>
          <ram:LineOne>1 Seller Street</ram:LineOne>
          <ram:CityName>Paris</ram:CityName>
          <ram:PostcodeCode>75001</ram:PostcodeCode>
          <ram:CountryID>FR</ram:CountryID>
        </ram:PostalTradeAddress>
      </ram:SellerTradeParty>
      <ram:BuyerTradeParty>
        <ram:Name>Buyer Corp</ram:Name>
        <ram:PostalTradeAddress>
          <ram:LineOne>2 Buyer Street</ram:LineOne>
          <ram:CityName>Lyon</ram:CityName>
          <ram:PostcodeCode>69001</ram:PostcodeCode>
          <ram:CountryID>FR</ram:CountryID>
        </ram:PostalTradeAddress>
      </ram:BuyerTradeParty>
    </ram:ApplicableHeaderTradeAgreement>
    <ram:IncludedSupplyChainTradeLineItem>
      <ram:SpecifiedTradeProduct><ram:Name>Service</ram:Name></ram:SpecifiedTradeProduct>
      <ram:SpecifiedLineTradeDelivery><ram:BilledQuantity unitCode="C62">1</ram:BilledQuantity></ram:SpecifiedLineTradeDelivery>
      <ram:SpecifiedLineTradeAgreement>
        <ram:NetPriceProductTradePrice><ram:ChargeAmount>100.00</ram:ChargeAmount></ram:NetPriceProductTradePrice>
      </ram:SpecifiedLineTradeAgreement>
      <ram:SpecifiedLineTradeSettlement>
        <ram:ApplicableTradeTax><ram:RateApplicablePercent>20.00</ram:RateApplicablePercent></ram:ApplicableTradeTax>
        <ram:SpecifiedTradeSettlementLineMonetarySummation><ram:LineTotalAmount>100.00</ram:LineTotalAmount></ram:SpecifiedTradeSettlementLineMonetarySummation>
      </ram:SpecifiedLineTradeSettlement>
    </ram:IncludedSupplyChainTradeLineItem>
    <ram:ApplicableHeaderTradeSettlement>
      <ram:InvoiceCurrencyCode>EUR</ram:InvoiceCurrencyCode>
      <ram:SpecifiedTradeSettlementHeaderMonetarySummation>
        <ram:TaxBasisTotalAmount>100.00</ram:TaxBasisTotalAmount>
        <ram:TaxTotalAmount>20.00</ram:TaxTotalAmount>
        <ram:GrandTotalAmount>120.00</ram:GrandTotalAmount>
        <ram:DuePayableAmount>120.00</ram:DuePayableAmount>
      </ram:SpecifiedTradeSettlementHeaderMonetarySummation>
    </ram:ApplicableHeaderTradeSettlement>
  </rsm:SupplyChainTradeTransaction>
</rsm:CrossIndustryInvoice>'''

    @patch('app.license.has_tier', return_value=False)
    @patch('app.metrics.metrics')
    def test_serialize_requires_license_403(self, mock_metrics, mock_has_tier):
        """Without a pro tier license, /serialize should return 403."""

        xml_content = b'''<?xml version="1.0" encoding="UTF-8"?>
        <rsm:CrossIndustryInvoice xmlns:rsm="urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100"
                                 xmlns:ram="urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100">
            <rsm:ExchangedDocument><ram:ID>INV-123</ram:ID></rsm:ExchangedDocument>
            <rsm:ExchangedDocumentContext>
                <ram:GuidelineSpecifiedDocumentContextParameter>
                    <ram:ID>urn:cen.eu:en16931:2017</ram:ID>
                </ram:GuidelineSpecifiedDocumentContextParameter>
            </rsm:ExchangedDocumentContext>
            <rsm:SupplyChainTradeTransaction>
                <ram:ApplicableHeaderTradeAgreement>
                    <ram:SellerTradeParty><ram:Name>Acme Corp</ram:Name></ram:SellerTradeParty>
                    <ram:BuyerTradeParty><ram:Name>Global Industries</ram:Name></ram:BuyerTradeParty>
                </ram:ApplicableHeaderTradeAgreement>
                <ram:ApplicableHeaderTradeSettlement>
                    <ram:SpecifiedTradeSettlementHeaderMonetarySummation>
                        <ram:TaxBasisTotalAmount>100.00</ram:TaxBasisTotalAmount>
                        <ram:TaxTotalAmount>20.00</ram:TaxTotalAmount>
                        <ram:GrandTotalAmount>120.00</ram:GrandTotalAmount>
                        <ram:DuePayableAmount>120.00</ram:DuePayableAmount>
                    </ram:SpecifiedTradeSettlementHeaderMonetarySummation>
                </ram:ApplicableHeaderTradeSettlement>
            </rsm:SupplyChainTradeTransaction>
        </rsm:CrossIndustryInvoice>'''

        response = self.client.post(
            "/v1/serialize",
            files={"file": ("test.xml", xml_content, "application/xml")}
        )
        data = response.json()
        self.assertEqual(response.status_code, 403)
        self.assertEqual(data["type"], "urn:facturx:error:license_required")

    @patch('app.license.is_licensed', return_value=True)
    @patch('app.license.has_tier', return_value=True)
    @patch('app.metrics.metrics')
    def test_serialize_ubl_xrechnung(self, mock_metrics, mock_has_tier, mock_is_licensed):
        """Pro users should be able to serialize UBL (XRechnung) files."""

        with patch.dict(os.environ, {"LICENSE_KEY": "valid-key"}):
            corpus_dir = Path(__file__).parent / "corpus" / "xrechnung-3.0.2-testsuite-2025-07-10" / "instances"
            ubl_file = None
            for f in corpus_dir.rglob("*.xml"):
                if b"CrossIndustryInvoice" not in f.read_bytes()[:500]:
                    ubl_file = f
                    break

            if not ubl_file:
                self.skipTest("No UBL file found in corpus for testing")

            content = ubl_file.read_bytes()

            response = self.client.post(
                "/v1/serialize",
                files={"file": (ubl_file.name, content, "application/xml")}
            )

            self.assertEqual(response.status_code, 200)
            data = response.json()
            if not data.get("success"):
                self.fail(f"UBL file serialization failed. Response: {json.dumps(data, indent=2)}")

            self.assertTrue(data["success"])
            self.assertEqual(data["invoice"]["format"], "ubl")
            self.assertTrue(data["invoice"]["profile"].startswith("xrechnung"))
            self.assertIsNotNone(data["invoice"]["invoice_number"])
            self.assertGreater(float(data["invoice"]["total_gross_amount"]), 0)
            self.assertEqual(data["schema_version"], "1.0.0")
            self.assertIn("engine_version", data)

            # New transparency fields are always present
            self.assertIn("fallbacks_applied", data)
            self.assertIsInstance(data["fallbacks_applied"], list)
            self.assertIn("xml_recovery_applied", data)
            self.assertIsInstance(data["xml_recovery_applied"], bool)

    @patch('app.license.is_licensed', return_value=True)
    @patch('app.license.has_tier', return_value=True)
    @patch('app.metrics.metrics')
    def test_serialize_clean_cii_has_empty_fallbacks(self, mock_metrics, mock_has_tier, mock_is_licensed):
        with patch.dict(os.environ, {"LICENSE_KEY": "valid-key"}):
            response = self.client.post(
                "/v1/serialize",
                files={"file": ("clean.xml", self._rich_cii_xml(), "application/xml")}
            )
            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertTrue(data["success"])
            self.assertIn("fallbacks_applied", data)
            self.assertEqual(data["fallbacks_applied"], [])
            self.assertIn("xml_recovery_applied", data)
            self.assertFalse(data["xml_recovery_applied"])

    def test_serialize_xml_recovery_flag_service_level(self):
        malformed = b'''<?xml version="1.0" encoding="UTF-8"?>
<rsm:CrossIndustryInvoice xmlns:rsm="urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100"
 xmlns:ram="urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100"
 xmlns:udt="urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100">
  <rsm:ExchangedDocumentContext><ram:GuidelineSpecifiedDocumentContextParameter><ram:ID>urn:cen.eu:en16931:2017</ram:ID></ram:GuidelineSpecifiedDocumentContextParameter></rsm:ExchangedDocumentContext>
  <rsm:ExchangedDocument><ram:ID>INV-RECOVER-1</ram:ID><ram:IssueDateTime><udt:DateTimeString>20260101</udt:DateTimeString></ram:IssueDateTime></rsm:ExchangedDocument>
  <rsm:SupplyChainTradeTransaction>
    <ram:ApplicableHeaderTradeAgreement>
      <ram:SellerTradeParty><ram:Name>Seller<ram:Name><ram:PostalTradeAddress><ram:LineOne>X</ram:LineOne><ram:CityName>Paris</ram:CityName><ram:PostcodeCode>75001</ram:PostcodeCode><ram:CountryID>FR</ram:CountryID></ram:PostalTradeAddress></ram:SellerTradeParty>
      <ram:BuyerTradeParty><ram:Name>Buyer</ram:Name><ram:PostalTradeAddress><ram:LineOne>Y</ram:LineOne><ram:CityName>Lyon</ram:CityName><ram:PostcodeCode>69001</ram:PostcodeCode><ram:CountryID>FR</ram:CountryID></ram:PostalTradeAddress></ram:BuyerTradeParty>
    </ram:ApplicableHeaderTradeAgreement>
    <ram:ApplicableHeaderTradeSettlement><ram:InvoiceCurrencyCode>EUR</ram:InvoiceCurrencyCode><ram:SpecifiedTradeSettlementHeaderMonetarySummation><ram:TaxBasisTotalAmount>100</ram:TaxBasisTotalAmount><ram:TaxTotalAmount>20</ram:TaxTotalAmount><ram:GrandTotalAmount>120</ram:GrandTotalAmount><ram:DuePayableAmount>120</ram:DuePayableAmount></ram:SpecifiedTradeSettlementHeaderMonetarySummation></ram:ApplicableHeaderTradeSettlement>
  </rsm:SupplyChainTradeTransaction>
</rsm:CrossIndustryInvoice>'''

        _, fallbacks, xml_recovery_applied = BusinessReadySerializer.serialize_with_diagnostics(malformed)
        self.assertTrue(xml_recovery_applied)
        self.assertTrue(any(f.get("fallback_type") == "xml_parser_recovery" for f in fallbacks))

    def test_serialize_fallback_entries_follow_contract(self):
        xml_with_missing_country = self._rich_cii_xml().replace(
            b"<ram:CountryID>FR</ram:CountryID>",
            b"",
            1,
        )

        _, fallbacks, _ = BusinessReadySerializer.serialize_with_diagnostics(xml_with_missing_country)
        self.assertTrue(fallbacks)

        allowed_types = {
            "default_value",
            "placeholder_value",
            "derived_value",
            "coercion",
            "xml_parser_recovery",
            "line_skipped",
            "line_truncated",
        }
        allowed_states = {"missing", "invalid", "malformed", "unparseable", "truncated"}

        for entry in fallbacks:
            self.assertEqual(
                set(entry.keys()),
                {"field", "fallback_type", "original_state", "applied_value"},
            )
            self.assertIn(entry["fallback_type"], allowed_types)
            self.assertIn(entry["original_state"], allowed_states)

    @patch('app.license.is_licensed', return_value=True)
    @patch('app.license.has_tier', return_value=True)
    @patch('app.metrics.metrics')
    def test_serialize_error_contains_schema_version(self, mock_metrics, mock_has_tier, mock_is_licensed):
        """Even on serialization errors, response must contain schema_version and engine_version."""

        with patch.dict(os.environ, {"LICENSE_KEY": "valid-key"}):
            invalid_xml = b'''<?xml version="1.0" encoding="UTF-8"?>
            <SomeRandomDocument>
                <Data>This is not a valid invoice format</Data>
            </SomeRandomDocument>'''

            response = self.client.post(
                "/v1/serialize",
                files={"file": ("invalid.xml", invalid_xml, "application/xml")}
            )

            self.assertEqual(response.status_code, 200)
            data = response.json()
            self.assertFalse(data["success"])
            self.assertEqual(data["schema_version"], "1.0.0")
            self.assertIn("engine_version", data)
            self.assertGreater(len(data["errors"]), 0)
            self.assertIn("fallbacks_applied", data)
            self.assertEqual(data["fallbacks_applied"], [])
            self.assertIn("xml_recovery_applied", data)
            self.assertFalse(data["xml_recovery_applied"])


if __name__ == "__main__":
    unittest.main()
