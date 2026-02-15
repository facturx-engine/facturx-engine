import pytest
from app.services.smart_diagnostics import SmartDiagnosticsEngine

@pytest.fixture
def engine():
    return SmartDiagnosticsEngine()

def test_proactive_scan_vat_country_mismatch(engine):
    """Test BR-CO-09-EXT: VAT prefix must match seller country."""
    xml = """
    <rsm:CrossIndustryInvoice xmlns:rsm="urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100" xmlns:ram="urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100">
        <rsm:SupplyChainTradeTransaction>
            <ram:ApplicableHeaderTradeAgreement>
                <ram:SellerTradeParty>
                    <ram:PostalTradeAddress>
                        <ram:CountryID>DE</ram:CountryID>
                    </ram:PostalTradeAddress>
                    <ram:SpecifiedTaxRegistration>
                        <ram:ID schemeID="VA">FR12345678901</ram:ID>
                    </ram:SpecifiedTaxRegistration>
                </ram:SellerTradeParty>
            </ram:ApplicableHeaderTradeAgreement>
        </rsm:SupplyChainTradeTransaction>
    </rsm:CrossIndustryInvoice>
    """
    diagnostics = engine._proactive_scan(xml.encode('utf-8'))
    assert len(diagnostics) == 1
    assert diagnostics[0].rule_id == "BR-CO-09-EXT"
    assert diagnostics[0].title == "Incohérence Pays / TVA"

def test_proactive_scan_type_amount_mismatch(engine):
    """Test BT-3-CONTEXT: Negative total requires TypeCode 381 (Credit Note)."""
    xml = """
    <rsm:CrossIndustryInvoice xmlns:rsm="urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100" xmlns:ram="urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100">
        <rsm:ExchangedDocument>
            <ram:TypeCode>380</ram:TypeCode>
        </rsm:ExchangedDocument>
        <rsm:SupplyChainTradeTransaction>
            <ram:ApplicableHeaderTradeSettlement>
                <ram:SpecifiedTradeSettlementHeaderMonetarySummation>
                    <ram:GrandTotalAmount>-100.00</ram:GrandTotalAmount>
                </ram:SpecifiedTradeSettlementHeaderMonetarySummation>
            </ram:ApplicableHeaderTradeSettlement>
        </rsm:SupplyChainTradeTransaction>
    </rsm:CrossIndustryInvoice>
    """
    diagnostics = engine._proactive_scan(xml.encode('utf-8'))
    assert len(diagnostics) == 1
    assert diagnostics[0].rule_id == "BT-3-CONTEXT"
    assert diagnostics[0].title == "Type de Facture Incorrect (Avoir)"

def test_proactive_scan_invalid_char_in_id(engine):
    """Test BT-1-FORMAT: Invoice ID contains forbidden characters."""
    xml = """
    <rsm:CrossIndustryInvoice xmlns:rsm="urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100" xmlns:ram="urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100">
        <rsm:ExchangedDocument>
            <ram:ID>INV#123</ram:ID>
        </rsm:ExchangedDocument>
    </rsm:CrossIndustryInvoice>
    """
    diagnostics = engine._proactive_scan(xml.encode('utf-8'))
    assert len(diagnostics) == 1
    assert diagnostics[0].rule_id == "BT-1-FORMAT"
    assert diagnostics[0].title == "Caractères Interdits dans le Numéro"

def test_proactive_scan_robustness_missing_tags(engine):
    """Test robustness with missing or malformed tags (should not raise)."""
    # Case 1: SellerTradeParty missing CountryID
    xml1 = """
    <rsm:CrossIndustryInvoice xmlns:rsm="urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100" xmlns:ram="urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100">
        <rsm:SupplyChainTradeTransaction>
            <ram:ApplicableHeaderTradeAgreement>
                <ram:SellerTradeParty>
                    <ram:SpecifiedTaxRegistration>
                        <ram:ID schemeID="VA">FR12345678901</ram:ID>
                    </ram:SpecifiedTaxRegistration>
                </ram:SellerTradeParty>
            </ram:ApplicableHeaderTradeAgreement>
        </rsm:SupplyChainTradeTransaction>
    </rsm:CrossIndustryInvoice>
    """
    diagnostics1 = engine._proactive_scan(xml1.encode('utf-8'))
    assert len(diagnostics1) == 0

    # Case 2: Malformed total (not a number)
    xml2 = """
    <rsm:CrossIndustryInvoice xmlns:rsm="urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100" xmlns:ram="urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100">
        <rsm:ExchangedDocument>
            <ram:TypeCode>380</ram:TypeCode>
        </rsm:ExchangedDocument>
        <rsm:SupplyChainTradeTransaction>
            <ram:ApplicableHeaderTradeSettlement>
                <ram:SpecifiedTradeSettlementHeaderMonetarySummation>
                    <ram:GrandTotalAmount>NOT_A_NUMBER</ram:GrandTotalAmount>
                </ram:SpecifiedTradeSettlementHeaderMonetarySummation>
            </ram:ApplicableHeaderTradeSettlement>
        </rsm:SupplyChainTradeTransaction>
    </rsm:CrossIndustryInvoice>
    """
    diagnostics2 = engine._proactive_scan(xml2.encode('utf-8'))
    assert len(diagnostics2) == 0

def test_proactive_scan_happy_path(engine):
    """Test a valid invoice snippet returning no diagnostics."""
    xml = """
    <rsm:CrossIndustryInvoice xmlns:rsm="urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100" xmlns:ram="urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100">
        <rsm:ExchangedDocument>
            <ram:ID>INV-2023-001</ram:ID>
            <ram:TypeCode>380</ram:TypeCode>
        </rsm:ExchangedDocument>
        <rsm:SupplyChainTradeTransaction>
            <ram:ApplicableHeaderTradeAgreement>
                <ram:SellerTradeParty>
                    <ram:PostalTradeAddress>
                        <ram:CountryID>FR</ram:CountryID>
                    </ram:PostalTradeAddress>
                    <ram:SpecifiedTaxRegistration>
                        <ram:ID schemeID="VA">FR12345678901</ram:ID>
                    </ram:SpecifiedTaxRegistration>
                </ram:SellerTradeParty>
            </ram:ApplicableHeaderTradeAgreement>
            <ram:ApplicableHeaderTradeSettlement>
                <ram:SpecifiedTradeSettlementHeaderMonetarySummation>
                    <ram:GrandTotalAmount>100.00</ram:GrandTotalAmount>
                </ram:SpecifiedTradeSettlementHeaderMonetarySummation>
            </ram:ApplicableHeaderTradeSettlement>
        </rsm:SupplyChainTradeTransaction>
    </rsm:CrossIndustryInvoice>
    """
    diagnostics = engine._proactive_scan(xml.encode('utf-8'))
    assert len(diagnostics) == 0
