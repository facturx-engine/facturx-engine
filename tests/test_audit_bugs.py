from app.services.business_serializer import BusinessReadySerializer


def test_serializer_xrechnung_profile_detection():
    """
    Verify profile detection independently from strict mapping completeness.
    """
    # Create a minimal XRechnung 3.0.x XML
    xml_content = b"""<?xml version="1.0" encoding="UTF-8"?>
<rsm:CrossIndustryInvoice xmlns:rsm="urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100"
                           xmlns:ram="urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100"
                           xmlns:udt="urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100">
    <rsm:ExchangedDocumentContext>
        <ram:GuidelineSpecifiedDocumentContextParameter>
            <ram:ID>urn:xeinkauf.de:kosit:xrechnung_3.0</ram:ID>
        </ram:GuidelineSpecifiedDocumentContextParameter>
    </rsm:ExchangedDocumentContext>
    <rsm:ExchangedDocument>
        <ram:ID>INV-1</ram:ID>
        <ram:IssueDateTime><udt:DateTimeString>20260219</udt:DateTimeString></ram:IssueDateTime>
    </rsm:ExchangedDocument>
    <ram:SupplyChainTradeTransaction>
        <ram:ApplicableHeaderTradeAgreement>
            <ram:SellerTradeParty><ram:Name>Seller</ram:Name></ram:SellerTradeParty>
            <ram:BuyerTradeParty><ram:Name>Buyer</ram:Name></ram:BuyerTradeParty>
        </ram:ApplicableHeaderTradeAgreement>
        <ram:ApplicableHeaderTradeSettlement>
            <ram:SpecifiedTradeSettlementHeaderMonetarySummation>
                <ram:TaxBasisTotalAmount>100</ram:TaxBasisTotalAmount>
                <ram:TaxTotalAmount>20</ram:TaxTotalAmount>
                <ram:GrandTotalAmount>120</ram:GrandTotalAmount>
                <ram:DuePayableAmount>120</ram:DuePayableAmount>
            </ram:SpecifiedTradeSettlementHeaderMonetarySummation>
        </ram:ApplicableHeaderTradeSettlement>
    </ram:SupplyChainTradeTransaction>
</rsm:CrossIndustryInvoice>"""
    
    root = BusinessReadySerializer._parse_xml(xml_content)
    profile = BusinessReadySerializer._cii_profile(root)

    assert profile == "xrechnung_3.0"
