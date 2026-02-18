"""
Business-Ready JSON Serializer.
Transitions from XML (CII/UBL) to a normalized, high-precision JSON format.
Pro Feature: Supports UBL, CII, and automatic field translation.
"""
import logging
from decimal import Decimal
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
            tax_breakdown=BusinessReadySerializer._parse_cii_tax_breakdown(root),
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
    def _parse_cii_tax_breakdown(root: etree._Element) -> list:
        """Parse ApplicableTradeTax elements into TaxBreakdownSchema list."""
        ns = BusinessReadySerializer.NS_CII

        def xpath_text(el, path):
            res = el.xpath(path + '/text()', namespaces=ns)
            return res[0] if res else None

        tax_nodes = root.xpath(
            '//ram:ApplicableHeaderTradeSettlement/ram:ApplicableTradeTax',
            namespaces=ns
        )
        if not tax_nodes:
            tax_nodes = root.xpath('//ram:ApplicableTradeTax', namespaces=ns)

        breakdown = []
        for node in tax_nodes:
            try:
                breakdown.append(TaxBreakdownSchema(
                    category=xpath_text(node, 'ram:CategoryCode') or "S",
                    rate=Decimal(xpath_text(node, 'ram:RateApplicablePercent') or "0"),
                    basis_amount=Decimal(xpath_text(node, 'ram:BasisAmount') or "0"),
                    tax_amount=Decimal(xpath_text(node, 'ram:CalculatedAmount') or "0"),
                ))
            except Exception as e:
                logger.warning(f"Skipping malformed tax entry: {e}")

        return breakdown

    @staticmethod
    def _parse_ubl(root: etree._Element) -> BusinessReadyInvoice:
        """Parse UBL XML (XRechnung / Peppol)."""
        ns = BusinessReadySerializer.NS_UBL
        
        def xpath_first(el, path):
            res = el.xpath(path, namespaces=ns)
            return res[0].text if res and res[0].text else None

        # Basic Info
        inv_id = xpath_first(root, '//cbc:ID')
        date_str = xpath_first(root, '//cbc:IssueDate')
        try:
            inv_date = datetime.strptime(date_str, "%Y-%m-%d").date()
        except (ValueError, TypeError):
            inv_date = date.today()

        # Seller
        seller_nodes = root.xpath('//cac:AccountingSupplierParty/cac:Party', namespaces=ns)
        if not seller_nodes:
            raise ValueError("Invalid UBL: Missing AccountingSupplierParty (mandatory)")
        seller = BusinessReadySerializer._parse_ubl_party(seller_nodes[0])
        
        # Buyer
        buyer_nodes = root.xpath('//cac:AccountingCustomerParty/cac:Party', namespaces=ns)
        if not buyer_nodes:
            raise ValueError("Invalid UBL: Missing AccountingCustomerParty (mandatory)")
        buyer = BusinessReadySerializer._parse_ubl_party(buyer_nodes[0])

        # Lines
        line_items = []
        for line_node in root.xpath('//cac:InvoiceLine', namespaces=ns):
            try:
                line_items.append(BusinessReadySerializer._parse_ubl_line(line_node))
            except (IndexError, KeyError) as e:
                logger.warning(f"Skipping malformed UBL line item: {e}")

        # Totals
        legal_monetary_total = root.xpath('//cac:LegalMonetaryTotal', namespaces=ns)
        if not legal_monetary_total:
            raise ValueError("Invalid UBL: Missing LegalMonetaryTotal (mandatory)")
        total_node = legal_monetary_total[0]
        
        # Helper to extract from total_node with fallback
        def get_total(path):
            res = total_node.xpath(path, namespaces=ns)
            return Decimal(res[0].text) if res and res[0].text else Decimal("0")

        # Extract Tax Total (can be multiple, we take the first)
        tax_total_res = root.xpath('//cac:TaxTotal/cbc:TaxAmount/text()', namespaces=ns)
        tax_total = Decimal(tax_total_res[0]) if tax_total_res else Decimal("0")

        return BusinessReadyInvoice(
            invoice_number=inv_id or "UNKNOWN",
            invoice_date=inv_date,
            currency=xpath_first(root, '//cbc:DocumentCurrencyCode') or "EUR",
            seller=seller,
            buyer=buyer,
            line_items=line_items,
            tax_breakdown=BusinessReadySerializer._parse_ubl_tax_breakdown(root),
            total_net_amount=get_total('cbc:TaxExclusiveAmount'),
            total_tax_amount=tax_total,
            total_gross_amount=get_total('cbc:TaxInclusiveAmount'),
            amount_due=get_total('cbc:PayableAmount'),
            format="ubl",
            profile="xrechnung"
        )

    @staticmethod
    def _parse_ubl_party(node: etree._Element) -> PartySchema:
        ns = BusinessReadySerializer.NS_UBL
        
        # Helper for safer extraction
        def get_text(xpath):
            res = node.xpath(xpath, namespaces=ns)
            return res[0] if res else None

        name = get_text('cac:PartyName/cbc:Name/text()') or \
               get_text('cac:PartyLegalEntity/cbc:RegistrationName/text()') or "Unknown"

        return PartySchema(
            name=name,
            vat_number=get_text('cac:PartyTaxScheme/cbc:CompanyID/text()'),
            address=AddressSchema(
                line1=get_text('cac:PostalAddress/cbc:StreetName/text()') or "...",
                city=get_text('cac:PostalAddress/cbc:CityName/text()') or "...",
                postcode=get_text('cac:PostalAddress/cbc:PostalZone/text()') or "...",
                country_code=get_text('cac:PostalAddress/cac:Country/cbc:IdentificationCode/text()') or "FR"
            )
        )

    @staticmethod
    def _parse_ubl_line(node: etree._Element) -> LineItemSchema:
        ns = BusinessReadySerializer.NS_UBL
        
        name = node.xpath('cac:Item/cbc:Name/text()', namespaces=ns)[0]
        qty = Decimal(node.xpath('cbc:InvoicedQuantity/text()', namespaces=ns)[0] or "1")
        price = Decimal(node.xpath('cac:Price/cbc:PriceAmount/text()', namespaces=ns)[0] or "0")
        total = Decimal(node.xpath('cbc:LineExtensionAmount/text()', namespaces=ns)[0] or "0")
        
        return LineItemSchema(
            name=name,
            quantity=qty,
            unit_code=node.xpath('cbc:InvoicedQuantity/@unitCode', namespaces=ns)[0] if node.xpath('cbc:InvoicedQuantity/@unitCode', namespaces=ns) else "C62",
            net_price=price,
            line_total=total,
            vat_rate=Decimal(node.xpath('cac:Item/cac:ClassifiedTaxCategory/cbc:Percent/text()', namespaces=ns)[0] or "0")
        )

    @staticmethod
    def _parse_ubl_tax_breakdown(root: etree._Element) -> list:
        """Parse TaxSubtotal elements into TaxBreakdownSchema list."""
        ns = BusinessReadySerializer.NS_UBL

        def xpath_text(el, path):
            res = el.xpath(path + '/text()', namespaces=ns)
            return res[0] if res else None

        tax_nodes = root.xpath('//cac:TaxTotal/cac:TaxSubtotal', namespaces=ns)
        
        breakdown = []
        for node in tax_nodes:
            try:
                breakdown.append(TaxBreakdownSchema(
                    category=xpath_text(node, 'cac:TaxCategory/cbc:ID') or "S",
                    rate=Decimal(xpath_text(node, 'cac:TaxCategory/cbc:Percent') or "0"),
                    basis_amount=Decimal(xpath_text(node, 'cbc:TaxableAmount') or "0"),
                    tax_amount=Decimal(xpath_text(node, 'cbc:TaxAmount') or "0"),
                ))
            except Exception as e:
                logger.warning(f"Skipping malformed UBL tax entry: {e}")

        return breakdown

    @staticmethod
    def _obfuscate(invoice: BusinessReadyInvoice) -> BusinessReadyInvoice:
        """Mask sensitive data for trial users."""
        
        def mask_string(s: str) -> str:
            if not s or len(s) < 3:
                return "***"
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
