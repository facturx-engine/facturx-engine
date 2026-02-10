import unittest
import html
from app.services.smart_diagnostics import SmartDiagnosticsEngine

class TestSmartDiagnosticsProactive(unittest.TestCase):
    def setUp(self):
        self.engine = SmartDiagnosticsEngine()

    def _get_xml(self, vat_id=None, country_id=None, type_code=None, grand_total=None, invoice_id=None):
        """Helper to generate XML for testing proactive scan using robust string template."""
        rsm_ns = "urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100"
        ram_ns = "urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100"

        # Escape values for XML
        evat_id = html.escape(vat_id) if vat_id is not None else None
        ecountry_id = html.escape(country_id) if country_id is not None else None
        etype_code = html.escape(type_code) if type_code is not None else None
        egrand_total = html.escape(grand_total) if grand_total is not None else None
        einvoice_id = html.escape(invoice_id) if invoice_id is not None else None

        xml = f'<?xml version="1.0" encoding="UTF-8"?>\n'
        xml += f'<rsm:CrossIndustryInvoice xmlns:rsm="{rsm_ns}" xmlns:ram="{ram_ns}">\n'

        if etype_code is not None or einvoice_id is not None:
            xml += '  <rsm:ExchangedDocument>\n'
            if einvoice_id is not None:
                xml += f'    <ram:ID>{einvoice_id}</ram:ID>\n'
            if etype_code is not None:
                xml += f'    <ram:TypeCode>{etype_code}</ram:TypeCode>\n'
            xml += '  </rsm:ExchangedDocument>\n'

        xml += '  <rsm:SupplyChainTradeTransaction>\n'

        if evat_id is not None or ecountry_id is not None:
            xml += '    <ram:ApplicableHeaderTradeAgreement>\n'
            xml += '      <ram:SellerTradeParty>\n'
            if ecountry_id is not None:
                xml += f'        <ram:PostalTradeAddress><ram:CountryID>{ecountry_id}</ram:CountryID></ram:PostalTradeAddress>\n'
            if evat_id is not None:
                xml += f'        <ram:SpecifiedTaxRegistration><ram:ID schemeID="VA">{evat_id}</ram:ID></ram:SpecifiedTaxRegistration>\n'
            xml += '      </ram:SellerTradeParty>\n'
            xml += '    </ram:ApplicableHeaderTradeAgreement>\n'

        if egrand_total is not None:
            xml += '    <ram:ApplicableHeaderTradeSettlement>\n'
            xml += '      <ram:SpecifiedTradeSettlementHeaderMonetarySummation>\n'
            xml += f'        <ram:GrandTotalAmount>{egrand_total}</ram:GrandTotalAmount>\n'
            xml += '      </ram:SpecifiedTradeSettlementHeaderMonetarySummation>\n'
            xml += '    </ram:ApplicableHeaderTradeSettlement>\n'

        xml += '  </rsm:SupplyChainTradeTransaction>\n'
        xml += '</rsm:CrossIndustryInvoice>'
        return xml.encode('utf-8')

    # -------------------------------------------------------------------------
    # 1. SIRET vs TVA Prefix Tests
    # -------------------------------------------------------------------------

    def test_vat_country_match_happy_path(self):
        """VAT ID starts with Country ID - should NOT trigger diagnostic."""
        xml = self._get_xml(vat_id="FR123", country_id="FR")
        diagnostics = self.engine.analyze([], xml_content=xml)
        ids = [d.rule_id for d in diagnostics]
        self.assertNotIn("BR-CO-09-EXT", ids)

    def test_vat_country_mismatch(self):
        """VAT ID does NOT start with Country ID - should trigger BR-CO-09-EXT."""
        xml = self._get_xml(vat_id="DE123", country_id="FR")
        diagnostics = self.engine.analyze([], xml_content=xml)
        ids = [d.rule_id for d in diagnostics]
        self.assertIn("BR-CO-09-EXT", ids)

    def test_vat_country_missing_vat(self):
        """VAT ID is missing - should NOT trigger diagnostic."""
        xml = self._get_xml(country_id="FR")
        diagnostics = self.engine.analyze([], xml_content=xml)
        ids = [d.rule_id for d in diagnostics]
        self.assertNotIn("BR-CO-09-EXT", ids)

    def test_vat_country_missing_country(self):
        """Country ID is missing - should NOT trigger diagnostic."""
        xml = self._get_xml(vat_id="FR123")
        diagnostics = self.engine.analyze([], xml_content=xml)
        ids = [d.rule_id for d in diagnostics]
        self.assertNotIn("BR-CO-09-EXT", ids)

    def test_vat_country_empty_values(self):
        """VAT or Country ID are empty - should NOT trigger diagnostic."""
        xml = self._get_xml(vat_id="", country_id="")
        diagnostics = self.engine.analyze([], xml_content=xml)
        ids = [d.rule_id for d in diagnostics]
        self.assertNotIn("BR-CO-09-EXT", ids)

    # -------------------------------------------------------------------------
    # 2. Negative Total vs Type Code Tests
    # -------------------------------------------------------------------------

    def test_negative_total_wrong_type(self):
        """Negative total with TypeCode 380 - should trigger BT-3-CONTEXT."""
        xml = self._get_xml(type_code="380", grand_total="-100.00")
        diagnostics = self.engine.analyze([], xml_content=xml)
        ids = [d.rule_id for d in diagnostics]
        self.assertIn("BT-3-CONTEXT", ids)

    def test_negative_total_correct_type(self):
        """Negative total with TypeCode 381 - should NOT trigger diagnostic."""
        xml = self._get_xml(type_code="381", grand_total="-100.00")
        diagnostics = self.engine.analyze([], xml_content=xml)
        ids = [d.rule_id for d in diagnostics]
        self.assertNotIn("BT-3-CONTEXT", ids)

    def test_positive_total_standard_type(self):
        """Positive total with TypeCode 380 - should NOT trigger diagnostic."""
        xml = self._get_xml(type_code="380", grand_total="100.00")
        diagnostics = self.engine.analyze([], xml_content=xml)
        ids = [d.rule_id for d in diagnostics]
        self.assertNotIn("BT-3-CONTEXT", ids)

    def test_invalid_decimal_total(self):
        """Invalid decimal in total - should be handled gracefully (no diagnostic)."""
        xml = self._get_xml(type_code="380", grand_total="NOT_A_NUMBER")
        # Should not raise exception
        diagnostics = self.engine.analyze([], xml_content=xml)
        ids = [d.rule_id for d in diagnostics]
        self.assertNotIn("BT-3-CONTEXT", ids)

    # -------------------------------------------------------------------------
    # 3. Invoice ID Format Tests
    # -------------------------------------------------------------------------

    def test_invoice_id_forbidden_chars(self):
        """Invoice ID with forbidden characters - should trigger BT-1-FORMAT."""
        # Testing multiple forbidden chars
        for char in ['#', '@', '&', '<', '>', '(', ')', '%', '$', '!']:
            with self.subTest(char=char):
                xml = self._get_xml(invoice_id=f"INV{char}123")
                diagnostics = self.engine.analyze([], xml_content=xml)
                ids = [d.rule_id for d in diagnostics]
                self.assertIn("BT-1-FORMAT", ids, f"Failed for character: {char}")

    def test_invoice_id_allowed_chars(self):
        """Invoice ID with allowed characters (A-Z, 0-9, /, -, _) - should NOT trigger."""
        allowed_id = "INV-2026/02_001"
        xml = self._get_xml(invoice_id=allowed_id)
        diagnostics = self.engine.analyze([], xml_content=xml)
        ids = [d.rule_id for d in diagnostics]
        self.assertNotIn("BT-1-FORMAT", ids)

    def test_invoice_id_empty(self):
        """Empty invoice ID - should NOT trigger BT-1-FORMAT."""
        xml = self._get_xml(invoice_id="")
        diagnostics = self.engine.analyze([], xml_content=xml)
        ids = [d.rule_id for d in diagnostics]
        self.assertNotIn("BT-1-FORMAT", ids)

    # -------------------------------------------------------------------------
    # 4. XML Parsing and Structure Edge Cases
    # -------------------------------------------------------------------------

    def test_malformed_xml_recovery(self):
        """Malformed XML should be handled gracefully due to recovery=True."""
        malformed_xml = b"<root><unclosed_tag>Data</root>"
        # Should not raise exception
        diagnostics = self.engine.analyze([], xml_content=malformed_xml)
        self.assertIsInstance(diagnostics, list)

    def test_missing_namespaces(self):
        """XML with missing expected namespaces - should not crash, just not find nodes."""
        xml = b'<?xml version="1.0" encoding="UTF-8"?><Invoice><ID>INV-123</ID></Invoice>'
        diagnostics = self.engine.analyze([], xml_content=xml)
        self.assertEqual(len(diagnostics), 0)

    def test_missing_expected_nodes(self):
        """Valid XML but missing nodes checked by proactive scan."""
        xml = b'<?xml version="1.0" encoding="UTF-8"?><rsm:CrossIndustryInvoice xmlns:rsm="urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100"></rsm:CrossIndustryInvoice>'
        diagnostics = self.engine.analyze([], xml_content=xml)
        self.assertEqual(len(diagnostics), 0)

if __name__ == "__main__":
    unittest.main()
