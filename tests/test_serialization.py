import unittest
from unittest.mock import patch

from fastapi.testclient import TestClient

from app.main import app
from app.services.business_serializer import (
    BusinessReadySerializer,
    SerializationMappingError,
)

FULL_VALIDATION = {
    "is_valid": True,
    "validation_completeness": "full",
    "errors": [],
    "layers_executed": ["xsd", "schematron"],
    "layers_skipped": [],
}


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
    <ram:TypeCode>380</ram:TypeCode>
    <ram:IssueDateTime><udt:DateTimeString format="102">20260101</udt:DateTimeString></ram:IssueDateTime>
  </rsm:ExchangedDocument>
  <rsm:SupplyChainTradeTransaction>
    <ram:ApplicableHeaderTradeAgreement>
      <ram:SellerTradeParty>
        <ram:Name>Seller Corp</ram:Name>
        <ram:PostalTradeAddress><ram:LineOne>1 Seller Street</ram:LineOne><ram:CityName>Paris</ram:CityName><ram:PostcodeCode>75001</ram:PostcodeCode><ram:CountryID>FR</ram:CountryID></ram:PostalTradeAddress>
      </ram:SellerTradeParty>
      <ram:BuyerTradeParty>
        <ram:Name>Buyer Corp</ram:Name>
        <ram:PostalTradeAddress><ram:LineOne>2 Buyer Street</ram:LineOne><ram:CityName>Lyon</ram:CityName><ram:PostcodeCode>69001</ram:PostcodeCode><ram:CountryID>FR</ram:CountryID></ram:PostalTradeAddress>
      </ram:BuyerTradeParty>
    </ram:ApplicableHeaderTradeAgreement>
    <ram:IncludedSupplyChainTradeLineItem>
      <ram:AssociatedDocumentLineDocument><ram:LineID>1</ram:LineID></ram:AssociatedDocumentLineDocument>
      <ram:SpecifiedTradeProduct><ram:Name>Service</ram:Name></ram:SpecifiedTradeProduct>
      <ram:SpecifiedLineTradeAgreement><ram:NetPriceProductTradePrice><ram:ChargeAmount>100.00</ram:ChargeAmount></ram:NetPriceProductTradePrice></ram:SpecifiedLineTradeAgreement>
      <ram:SpecifiedLineTradeDelivery><ram:BilledQuantity unitCode="C62">1</ram:BilledQuantity></ram:SpecifiedLineTradeDelivery>
      <ram:SpecifiedLineTradeSettlement>
        <ram:ApplicableTradeTax><ram:CategoryCode>S</ram:CategoryCode><ram:RateApplicablePercent>20.00</ram:RateApplicablePercent></ram:ApplicableTradeTax>
        <ram:SpecifiedTradeSettlementLineMonetarySummation><ram:LineTotalAmount>100.00</ram:LineTotalAmount></ram:SpecifiedTradeSettlementLineMonetarySummation>
      </ram:SpecifiedLineTradeSettlement>
    </ram:IncludedSupplyChainTradeLineItem>
    <ram:ApplicableHeaderTradeSettlement>
      <ram:InvoiceCurrencyCode>EUR</ram:InvoiceCurrencyCode>
      <ram:ApplicableTradeTax><ram:CalculatedAmount>20.00</ram:CalculatedAmount><ram:TypeCode>VAT</ram:TypeCode><ram:BasisAmount>100.00</ram:BasisAmount><ram:CategoryCode>S</ram:CategoryCode><ram:RateApplicablePercent>20.00</ram:RateApplicablePercent></ram:ApplicableTradeTax>
      <ram:SpecifiedTradeSettlementHeaderMonetarySummation><ram:TaxBasisTotalAmount>100.00</ram:TaxBasisTotalAmount><ram:TaxTotalAmount>20.00</ram:TaxTotalAmount><ram:GrandTotalAmount>120.00</ram:GrandTotalAmount><ram:DuePayableAmount>120.00</ram:DuePayableAmount></ram:SpecifiedTradeSettlementHeaderMonetarySummation>
    </ram:ApplicableHeaderTradeSettlement>
  </rsm:SupplyChainTradeTransaction>
</rsm:CrossIndustryInvoice>'''

    @staticmethod
    def _rich_ubl_xml() -> bytes:
        return b'''<?xml version="1.0" encoding="UTF-8"?>
<Invoice xmlns="urn:oasis:names:specification:ubl:schema:xsd:Invoice-2"
 xmlns:cac="urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2"
 xmlns:cbc="urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2">
  <cbc:CustomizationID>urn:cen.eu:en16931:2017</cbc:CustomizationID>
  <cbc:ID>UBL-001</cbc:ID><cbc:IssueDate>2026-01-01</cbc:IssueDate><cbc:DueDate>2026-01-31</cbc:DueDate><cbc:InvoiceTypeCode>380</cbc:InvoiceTypeCode><cbc:DocumentCurrencyCode>EUR</cbc:DocumentCurrencyCode>
  <cac:AccountingSupplierParty><cac:Party><cbc:EndpointID schemeID="0204">seller</cbc:EndpointID><cac:PartyName><cbc:Name>Seller GmbH</cbc:Name></cac:PartyName><cac:PostalAddress><cbc:StreetName>Main Street 1</cbc:StreetName><cbc:CityName>Berlin</cbc:CityName><cbc:PostalZone>10115</cbc:PostalZone><cac:Country><cbc:IdentificationCode>DE</cbc:IdentificationCode></cac:Country></cac:PostalAddress></cac:Party></cac:AccountingSupplierParty>
  <cac:AccountingCustomerParty><cac:Party><cbc:EndpointID schemeID="0204">buyer</cbc:EndpointID><cac:PartyName><cbc:Name>Buyer GmbH</cbc:Name></cac:PartyName><cac:PostalAddress><cbc:StreetName>Other Street 2</cbc:StreetName><cbc:CityName>Hamburg</cbc:CityName><cbc:PostalZone>20095</cbc:PostalZone><cac:Country><cbc:IdentificationCode>DE</cbc:IdentificationCode></cac:Country></cac:PostalAddress></cac:Party></cac:AccountingCustomerParty>
  <cac:TaxTotal><cbc:TaxAmount currencyID="EUR">19.00</cbc:TaxAmount><cac:TaxSubtotal><cbc:TaxableAmount currencyID="EUR">100.00</cbc:TaxableAmount><cbc:TaxAmount currencyID="EUR">19.00</cbc:TaxAmount><cac:TaxCategory><cbc:ID>S</cbc:ID><cbc:Percent>19.00</cbc:Percent></cac:TaxCategory></cac:TaxSubtotal></cac:TaxTotal>
  <cac:LegalMonetaryTotal><cbc:TaxExclusiveAmount currencyID="EUR">100.00</cbc:TaxExclusiveAmount><cbc:TaxInclusiveAmount currencyID="EUR">119.00</cbc:TaxInclusiveAmount><cbc:PayableAmount currencyID="EUR">119.00</cbc:PayableAmount></cac:LegalMonetaryTotal>
  <cac:InvoiceLine><cbc:ID>1</cbc:ID><cbc:InvoicedQuantity unitCode="C62">1</cbc:InvoicedQuantity><cbc:LineExtensionAmount currencyID="EUR">100.00</cbc:LineExtensionAmount><cac:Item><cbc:Name>Service</cbc:Name><cac:ClassifiedTaxCategory><cbc:ID>S</cbc:ID><cbc:Percent>19.00</cbc:Percent></cac:ClassifiedTaxCategory></cac:Item><cac:Price><cbc:PriceAmount currencyID="EUR">100.00</cbc:PriceAmount></cac:Price></cac:InvoiceLine>
</Invoice>'''

    @patch("app.license.has_tier", return_value=False)
    @patch("app.metrics.metrics")
    def test_serialize_requires_license_403(self, mock_metrics, mock_has_tier):
        response = self.client.post(
            "/v1/serialize",
            files={"file": ("test.xml", self._rich_cii_xml(), "application/xml")},
        )
        self.assertEqual(response.status_code, 403)
        self.assertEqual(response.json()["type"], "urn:facturx:error:feature_not_enabled")

    @patch("app.services.hybrid_validation_service.HybridValidationService.validate", return_value=FULL_VALIDATION)
    @patch("app.license.is_licensed", return_value=True)
    @patch("app.license.has_tier", return_value=True)
    @patch("app.metrics.metrics")
    def test_serialize_clean_cii_is_strict_success(self, mock_metrics, mock_has_tier, mock_is_licensed, mock_validate):
        response = self.client.post(
            "/v1/serialize",
            files={"file": ("clean.xml", self._rich_cii_xml(), "application/xml")},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertTrue(data["success"])
        self.assertEqual(data["schema_version"], "2.0.0")
        self.assertEqual(data["mapping_status"], "complete")
        self.assertEqual(data["validation_status"], "passed")
        self.assertEqual(data["suggested_route"], "continue_client_checks")
        self.assertEqual(data["invoice"]["format"], "cii")
        self.assertNotIn("fallbacks_applied", data)
        self.assertNotIn("xml_recovery_applied", data)

    @patch("app.services.hybrid_validation_service.HybridValidationService.validate", return_value=FULL_VALIDATION)
    @patch("app.license.is_licensed", return_value=True)
    @patch("app.license.has_tier", return_value=True)
    @patch("app.metrics.metrics")
    def test_serialize_ubl(self, mock_metrics, mock_has_tier, mock_is_licensed, mock_validate):
        response = self.client.post(
            "/v1/serialize",
            files={"file": ("invoice.xml", self._rich_ubl_xml(), "application/xml")},
        )
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(data["invoice"]["format"], "ubl")
        self.assertEqual(data["invoice"]["invoice_number"], "UBL-001")
        self.assertEqual(data["invoice"]["document_type_code"], "380")

    def test_malformed_xml_is_never_recovered(self):
        malformed = self._rich_cii_xml().replace(b"</ram:Name>", b"<ram:Name>", 1)
        with self.assertRaises(SerializationMappingError) as context:
            BusinessReadySerializer.serialize(malformed)
        self.assertEqual(context.exception.diagnostics[0].code, "XML_MALFORMED")

    def test_missing_optional_country_stays_null(self):
        xml = self._rich_cii_xml().replace(b"<ram:CountryID>FR</ram:CountryID>", b"", 1)
        invoice, fallbacks, recovered = BusinessReadySerializer.serialize_with_diagnostics(xml)
        self.assertIsNone(invoice.seller.address.country_code)
        self.assertEqual(fallbacks, [])
        self.assertFalse(recovered)

    def test_missing_required_currency_is_rejected(self):
        xml = self._rich_cii_xml().replace(
            b"<ram:InvoiceCurrencyCode>EUR</ram:InvoiceCurrencyCode>", b""
        )
        with self.assertRaises(SerializationMappingError) as context:
            BusinessReadySerializer.serialize(xml)
        self.assertEqual(
            context.exception.diagnostics[0].code,
            "MAPPING_REQUIRED_VALUE_MISSING",
        )

    def test_unsupported_material_element_is_not_silently_ignored(self):
        xml = self._rich_cii_xml().replace(
            b"<ram:InvoiceCurrencyCode>EUR</ram:InvoiceCurrencyCode>",
            b"<ram:SpecifiedTradeAllowanceCharge/><ram:InvoiceCurrencyCode>EUR</ram:InvoiceCurrencyCode>",
        )
        with self.assertRaises(SerializationMappingError) as context:
            BusinessReadySerializer.serialize(xml)
        self.assertEqual(
            context.exception.diagnostics[0].code,
            "MAPPING_UNSUPPORTED_ELEMENT",
        )

    @patch("app.services.hybrid_validation_service.HybridValidationService.validate", return_value=FULL_VALIDATION)
    @patch("app.license.is_licensed", return_value=True)
    @patch("app.license.has_tier", return_value=True)
    @patch("app.metrics.metrics")
    def test_mapping_failure_returns_422(self, mock_metrics, mock_has_tier, mock_is_licensed, mock_validate):
        xml = self._rich_cii_xml().replace(
            b"<ram:InvoiceCurrencyCode>EUR</ram:InvoiceCurrencyCode>", b""
        )
        response = self.client.post(
            "/v1/serialize",
            files={"file": ("invalid.xml", xml, "application/xml")},
        )
        self.assertEqual(response.status_code, 422)
        data = response.json()
        self.assertFalse(data["success"])
        self.assertEqual(data["schema_version"], "2.0.0")
        self.assertEqual(data["validation_status"], "passed")
        self.assertEqual(data["mapping_status"], "failed")

    @patch(
        "app.services.hybrid_validation_service.HybridValidationService.validate",
        return_value={
            "is_valid": True,
            "validation_completeness": "partial",
            "errors": [],
            "layers_skipped": [{"layer": "schematron", "reason": "tool_missing:saxon_jar"}],
        },
    )
    @patch("app.license.is_licensed", return_value=True)
    @patch("app.license.has_tier", return_value=True)
    @patch("app.metrics.metrics")
    def test_incomplete_validation_returns_422(self, mock_metrics, mock_has_tier, mock_is_licensed, mock_validate):
        response = self.client.post(
            "/v1/serialize",
            files={"file": ("invoice.xml", self._rich_cii_xml(), "application/xml")},
        )
        self.assertEqual(response.status_code, 422)
        self.assertEqual(response.json()["validation_status"], "incomplete")


if __name__ == "__main__":
    unittest.main()
