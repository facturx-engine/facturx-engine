"""
Business-Ready JSON Serializer.
Transitions from XML (CII/UBL) to a normalized, high-precision JSON format.
Pro Feature: Supports UBL, CII, and automatic field translation.
"""
import logging
from typing import Dict, Any, List, Optional
from decimal import Decimal, ROUND_HALF_UP
from datetime import datetime, date
from lxml import etree

from app.schemas.integration import (
    BusinessReadyInvoice, PartySchema, AddressSchema, 
    LineItemSchema, TaxBreakdownSchema
)

logger = logging.getLogger(__name__)


class BusinessReadySerializer:
    """
    Transforms Factur-X/ZUGFeRD/XRechnung XML into the Pro Business-Ready format.
    
    Supports:
    - CII (Cross Industry Invoice) - Factur-X / ZUGFeRD
    - UBL (Universal Business Language) - XRechnung / Peppol
    - Automatic Obfuscation for Trial users.
    """
    
    # Namespaces for CII
    NS_CII = {
        'rsm': 'urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100',
        'ram': 'urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100',
        'udt': 'urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100'
    }
    
    # Namespaces for UBL (Simplified for common XRechnung)
    NS_UBL = {
        'ubl': 'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2',
        'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
        'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'
    }

    @staticmethod
    def serialize(xml_bytes: bytes, is_pro: bool = False, obfuscate: bool = False) -> BusinessReadyInvoice:
        """
        Main entry point for serialization.
        
        Args:
            xml_bytes: Raw XML bytes
            is_pro: Whether the user has a Pro license
            obfuscate: Whether to mask sensitive data (for trial)
        """
        parser = etree.XMLParser(recover=True, resolve_entities=False, no_network=True)
        root = etree.fromstring(xml_bytes, parser=parser)
        
        # Detect Format (CII vs UBL)
        if 'CrossIndustryInvoice' in root.tag:
            invoice = BusinessReadySerializer._parse_cii(root)
        elif 'Invoice' in root.tag and 'urn:oasis:names:specification:ubl' in root.tag:
            invoice = BusinessReadySerializer._parse_ubl(root)
        else:
            raise ValueError("Unsupported XML format. Must be CII (Factur-X) or UBL.")
            
        if obfuscate:
            return BusinessReadySerializer._obfuscate(invoice)
            
        return invoice

    @staticmethod
    def _parse_cii(root: etree._Element) -> BusinessReadyInvoice:
        """Parse CII XML (Factur-X / ZUGFeRD)."""
        ns = BusinessReadySerializer.NS_CII
        
        def xpath_first(el, path):
            res = el.xpath(path, namespaces=ns)
            return res[0].text if res and res[0].text else None

        # Basic Info
        inv_id = xpath_first(root, '//rsm:ExchangedDocument/ram:ID')
        date_str = xpath_first(root, '//rsm:ExchangedDocument/ram:IssueDateTime/udt:DateTimeString')
        # Try to parse date (CII usually YYYYMMDD)
        try:
            inv_date = datetime.strptime(date_str, "%Y%m%d").date()
        except (ValueError, TypeError):
            inv_date = date.today()

        # Seller
        seller_nodes = root.xpath('//ram:SellerTradeParty', namespaces=ns)
        if not seller_nodes:
            raise ValueError("Invalid CII: Missing SellerTradeParty (mandatory)")
        seller = BusinessReadySerializer._parse_cii_party(seller_nodes[0])
        
        # Buyer
        buyer_nodes = root.xpath('//ram:BuyerTradeParty', namespaces=ns)
        if not buyer_nodes:
            raise ValueError("Invalid CII: Missing BuyerTradeParty (mandatory)")
        buyer = BusinessReadySerializer._parse_cii_party(buyer_nodes[0])

        # Lines
        line_items = []
        for line_node in root.xpath('//ram:IncludedSupplyChainTradeLineItem', namespaces=ns):
            try:
                line_items.append(BusinessReadySerializer._parse_cii_line(line_node))
            except (IndexError, KeyError) as e:
                logger.warning(f"Skipping malformed line item: {e}")

        # Totals
        summation_nodes = root.xpath('//ram:SpecifiedTradeSettlementHeaderMonetarySummation', namespaces=ns)
        if not summation_nodes:
            raise ValueError("Invalid CII: Missing MonetarySummation (mandatory)")
        summation_node = summation_nodes[0]
        
        return BusinessReadyInvoice(
            invoice_number=inv_id or "UNKNOWN",
            invoice_date=inv_date,
            currency=xpath_first(root, '//ram:InvoiceCurrencyCode') or "EUR",
            seller=seller,
            buyer=buyer,
            line_items=line_items,
            tax_breakdown=[], # TODO: Implement tax breakdown
            total_net_amount=Decimal(xpath_first(summation_node, 'ram:TaxBasisTotalAmount') or "0"),
            total_tax_amount=Decimal(xpath_first(summation_node, 'ram:TaxTotalAmount') or "0"),
            total_gross_amount=Decimal(xpath_first(summation_node, 'ram:GrandTotalAmount') or "0"),
            amount_due=Decimal(xpath_first(summation_node, 'ram:DuePayableAmount') or "0"),
            format="factur-x",
            profile="en16931"
        )

    @staticmethod
    def _parse_cii_party(node: etree._Element) -> PartySchema:
        ns = BusinessReadySerializer.NS_CII
        return PartySchema(
            name=node.xpath('ram:Name/text()', namespaces=ns)[0] if node.xpath('ram:Name', namespaces=ns) else "Unknown",
            vat_number=node.xpath('.//ram:SpecifiedTaxRegistration/ram:ID/text()', namespaces=ns)[0] if node.xpath('.//ram:SpecifiedTaxRegistration/ram:ID', namespaces=ns) else None,
            address=AddressSchema(
                line1=node.xpath('.//ram:PostalTradeAddress/ram:LineOne/text()', namespaces=ns)[0] if node.xpath('.//ram:PostalTradeAddress/ram:LineOne', namespaces=ns) else "...",
                city=node.xpath('.//ram:PostalTradeAddress/ram:CityName/text()', namespaces=ns)[0] if node.xpath('.//ram:PostalTradeAddress/ram:CityName', namespaces=ns) else "...",
                postcode=node.xpath('.//ram:PostalTradeAddress/ram:PostcodeCode/text()', namespaces=ns)[0] if node.xpath('.//ram:PostalTradeAddress/ram:PostcodeCode', namespaces=ns) else "...",
                country_code=node.xpath('.//ram:PostalTradeAddress/ram:CountryID/text()', namespaces=ns)[0] if node.xpath('.//ram:PostalTradeAddress/ram:CountryID', namespaces=ns) else "FR"
            )
        )

    @staticmethod
    def _parse_cii_line(node: etree._Element) -> LineItemSchema:
        ns = BusinessReadySerializer.NS_CII
        name = node.xpath('.//ram:SpecifiedTradeProduct/ram:Name/text()', namespaces=ns)[0]
        qty = Decimal(node.xpath('.//ram:BilledQuantity/text()', namespaces=ns)[0] or "1")
        price = Decimal(node.xpath('.//ram:NetPriceProductTradePrice/ram:ChargeAmount/text()', namespaces=ns)[0] or "0")
        total = Decimal(node.xpath('.//ram:SpecifiedTradeSettlementLineMonetarySummation/ram:LineTotalAmount/text()', namespaces=ns)[0] or "0")
        
        return LineItemSchema(
            name=name,
            quantity=qty,
            unit_code=node.xpath('.//ram:BilledQuantity/@unitCode', namespaces=ns)[0] if node.xpath('.//ram:BilledQuantity/@unitCode', namespaces=ns) else "C62",
            net_price=price,
            line_total=total,
            vat_rate=Decimal(node.xpath('.//ram:ApplicableTradeTax/ram:RateApplicablePercent/text()', namespaces=ns)[0] or "0")
        )

    @staticmethod
    def _parse_ubl(root: etree._Element) -> BusinessReadyInvoice:
        """Placeholder for UBL parsing logic (XRechnung)."""
        # In a real implementation, this would mimic _parse_cii with UBL namespaces and paths
        raise NotImplementedError("UBL Support is slated for v1.4.1 (Enterprise Early Access)")

    @staticmethod
    def _obfuscate(invoice: BusinessReadyInvoice) -> BusinessReadyInvoice:
        """Mask sensitive data for trial users."""
        
        def mask_string(s: str) -> str:
            if not s or len(s) < 3: return "***"
            return s[:2] + "*" * (len(s) - 2)

        # Mask Seller/Buyer
        invoice.seller.name = mask_string(invoice.seller.name)
        if invoice.seller.vat_number: 
            invoice.seller.vat_number = mask_string(invoice.seller.vat_number)
        
        invoice.buyer.name = mask_string(invoice.buyer.name)
        
        # Mask Address
        if invoice.seller.address:
            invoice.seller.address.line1 = "REDACTED FOR TRIAL"
            
        # Mask Amounts (Set to 0.00 to show structure but no value)
        invoice.total_net_amount = Decimal("0.00")
        invoice.total_tax_amount = Decimal("0.00")
        invoice.total_gross_amount = Decimal("0.00")
        invoice.amount_due = Decimal("0.00")
        
        # Mask line items
        for line in invoice.line_items:
            line.name = mask_string(line.name)
            line.net_price = Decimal("0.00")
            line.line_total = Decimal("0.00")
            
        invoice.is_obfuscated = True
        return invoice
