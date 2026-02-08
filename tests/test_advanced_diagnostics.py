import unittest
from decimal import Decimal
from app.services.smart_diagnostics import SmartDiagnosticsEngine

class TestAdvancedDiagnostics(unittest.TestCase):
    def setUp(self):
        self.engine = SmartDiagnosticsEngine()

    def test_siret_vat_mismatch(self):
        """SIRET/VAT prefix mismatch should be detected."""
        xml = b"""<?xml version="1.0" encoding="UTF-8"?>
        <rsm:CrossIndustryInvoice xmlns:rsm="urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100" 
                                 xmlns:ram="urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100">
            <rsm:SupplyChainTradeTransaction>
                <ram:ApplicableHeaderTradeAgreement>
                    <ram:SellerTradeParty>
                        <ram:PostalTradeAddress><ram:CountryID>FR</ram:CountryID></ram:PostalTradeAddress>
                        <ram:SpecifiedTaxRegistration><ram:ID schemeID="VA">DE123456789</ram:ID></ram:SpecifiedTaxRegistration>
                    </ram:SellerTradeParty>
                </ram:ApplicableHeaderTradeAgreement>
            </rsm:SupplyChainTradeTransaction>
        </rsm:CrossIndustryInvoice>"""
        
        diagnostics = self.engine.analyze([], xml_content=xml)
        ids = [d.rule_id for d in diagnostics]
        self.assertIn("BR-CO-09-EXT", ids)

    def test_negative_total_wrong_type(self):
        """Negative total with TypeCode 380 should be flagged."""
        xml = b"""<?xml version="1.0" encoding="UTF-8"?>
        <rsm:CrossIndustryInvoice xmlns:rsm="urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100" 
                                 xmlns:ram="urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100">
            <rsm:ExchangedDocument><ram:TypeCode>380</ram:TypeCode></rsm:ExchangedDocument>
            <rsm:SupplyChainTradeTransaction>
                <ram:ApplicableHeaderTradeSettlement>
                    <ram:SpecifiedTradeSettlementHeaderMonetarySummation>
                        <ram:GrandTotalAmount>-100.00</ram:GrandTotalAmount>
                    </ram:SpecifiedTradeSettlementHeaderMonetarySummation>
                </ram:ApplicableHeaderTradeSettlement>
            </rsm:SupplyChainTradeTransaction>
        </rsm:CrossIndustryInvoice>"""
        
        diagnostics = self.engine.analyze([], xml_content=xml)
        ids = [d.rule_id for d in diagnostics]
        self.assertIn("BT-3-CONTEXT", ids)

    def test_forbidden_chars_in_id(self):
        """Forbidden characters in Invoice ID should be flagged."""
        xml = b"""<?xml version="1.0" encoding="UTF-8"?>
        <rsm:CrossIndustryInvoice xmlns:rsm="urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100" 
                                 xmlns:ram="urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100">
            <rsm:ExchangedDocument><ram:ID>INV#123@2026</ram:ID></rsm:ExchangedDocument>
        </rsm:CrossIndustryInvoice>"""
        
        diagnostics = self.engine.analyze([], xml_content=xml)
        ids = [d.rule_id for d in diagnostics]
        self.assertIn("BT-1-FORMAT", ids)

    def test_rounding_tolerance_warning(self):
        """Small delta should trigger warning instead of error."""
        # 100.00 + 20.00 = 120.00. We declare 120.03. Delta = 0.03 (< 0.05 tolerance)
        xml = b"""<?xml version="1.0" encoding="UTF-8"?>
        <rsm:CrossIndustryInvoice xmlns:rsm="urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100" 
                                 xmlns:ram="urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100">
            <rsm:SupplyChainTradeTransaction>
                <ram:ApplicableHeaderTradeSettlement>
                    <ram:SpecifiedTradeSettlementHeaderMonetarySummation>
                        <ram:TaxBasisTotalAmount>100.00</ram:TaxBasisTotalAmount>
                        <ram:TaxTotalAmount>20.00</ram:TaxTotalAmount>
                        <ram:GrandTotalAmount>120.03</ram:GrandTotalAmount>
                    </ram:SpecifiedTradeSettlementHeaderMonetarySummation>
                </ram:ApplicableHeaderTradeSettlement>
            </rsm:SupplyChainTradeTransaction>
        </rsm:CrossIndustryInvoice>"""
        
        # We simulate that Schematron failed with BR-CO-14
        raw_errors = [{"rule_id": "BR-CO-14", "severity": "error", "message": "Total mismatch"}]
        diagnostics = self.engine.analyze(raw_errors, xml_content=xml)
        
        br14 = next(d for d in diagnostics if d.rule_id == "BR-CO-14")
        self.assertEqual(br14.severity, "warning")
        self.assertIn("Rounding difference detected", br14.explanation)

if __name__ == "__main__":
    unittest.main()
