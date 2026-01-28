"""
Extraction service for Community Edition (Open Core).
Parses Factur-X/ZUGFeRD XML and returns FULL invoice data (no obfuscation).
Pro edition adds advanced validation and compliance features.
"""
import logging
from io import BytesIO
from typing import Dict, Any, List
from lxml import etree
from facturx import get_xml_from_pdf, get_level, get_flavor
import hashlib

logger = logging.getLogger(__name__)

class ExtractionService:
    """
    Community Edition Extractor.
    Parses Factur-X/ZUGFeRD XML and generates a coherent DEMO invoice structure.
    """

    _SECURE_PARSER = etree.XMLParser(
        resolve_entities=False,
        no_network=True,
        huge_tree=False,
        recover=False  # Security: strict parsing
    )

    @staticmethod
    def extract_invoice_data(file_content: bytes, filename: str) -> Dict[str, Any]:
        result = {
            "format_detected": None,
            "profile_detected": None,
            "xml_extracted": False,
            "invoice_json": None,
            "errors": []
        }
        
        try:
            # 1. PDF Check
            if not filename.lower().endswith('.pdf') and not file_content.startswith(b'%PDF'):
                result["errors"].append({"code": "NOT_A_PDF", "message": "File is not a PDF"})
                return result

            # 2. Extract XML
            try:
                xml_filename, xml_bytes = get_xml_from_pdf(BytesIO(file_content), check_xsd=False)
                if not xml_bytes:
                    result["format_detected"] = "not_facturx"
                    result["errors"].append({"code": "NO_XML", "message": "No Factur-X XML found"})
                    return result
                result["xml_extracted"] = True
            except Exception as e:
                result["format_detected"] = "not_facturx"
                result["errors"].append({"code": "EXTRACTION_FAIL", "message": str(e)})
                return result

            # 3. Parse XML
            try:
                xml_root = etree.fromstring(xml_bytes, parser=ExtractionService._SECURE_PARSER)
                result["format_detected"] = get_flavor(xml_root)
                result["profile_detected"] = get_level(xml_root)
                
                # 4. Map to Intelligent Demo JSON
                result["invoice_json"] = ExtractionService._parse_demo_invoice(xml_root, result["format_detected"], filename)
                
            except Exception as e:
                result["errors"].append({"code": "PARSE_ERROR", "message": str(e)})
                logger.exception("Parse error")
                
            return result
            
        except Exception as e:
            logger.exception(f"Internal error: {e}")
            result["errors"].append({"code": "INTERNAL_ERROR", "message": str(e)})
            return result

    @staticmethod
    def _parse_demo_invoice(xml_root, flavor, filename):
        # Namespaces
        if flavor in ('factur-x', 'facturx'):
            ns = {'rsm': 'urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100',
                  'ram': 'urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100',
                  'udt': 'urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100'}
        else:
            ns = {'rsm': 'urn:ferd:CrossIndustryDocument:invoice:1p0',
                  'ram': 'urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:12',
                  'udt': 'urn:un:unece:uncefact:data:standard:UnqualifiedDataType:15'}

        def xpath_first(el, paths):
            if isinstance(paths, str): paths = [paths]
            for p in paths:
                res = el.xpath(p, namespaces=ns)
                if res:
                    val = res[0]
                    return val.text if hasattr(val, 'text') else str(val)
            return None

        # --- SMART DEMO MAPPING ---
        
        # 1. Structure (Real)
        # 1. Structure (Real)
        # Use specific paths to avoid matching Profile ID (GuidelineSpecifiedDocumentContextParameter/ID)
        invoice_id = xpath_first(xml_root, [
            '//rsm:ExchangedDocument/ram:ID', # Standard CII
            '//rsm:HeaderExchangedDocument/ram:ID' # Old ZUGFeRD
        ])
        
        date_str = xpath_first(xml_root, [
            '//rsm:ExchangedDocument/ram:IssueDateTime/udt:DateTimeString', 
            '//rsm:HeaderExchangedDocument/ram:IssueDateTime/udt:DateTimeString', 
            '//ram:IssueDateTime/udt:DateTimeString'
        ])
        currency = xpath_first(xml_root, ['//ram:InvoiceCurrencyCode']) or "EUR"

        # 2. Line Items
        line_items = []
        items = xml_root.xpath('//ram:IncludedSupplyChainTradeLineItem', namespaces=ns)
        
        # NOTE: Profile 'minimum' usually has no line items. We do NOT fake them.
        warnings = []
        if not items:
             if 'minimum' in str(flavor).lower():
                 warnings.append({
                     "code": "NO_LINE_ITEMS_IN_XML",
                     "message": "Profile 'minimum' typically contains no line items."
                 })
             else:
                 warnings.append({
                     "code": "NO_LINE_ITEMS_IN_XML",
                     "message": "No line items found in XML."
                 })

        total_net = 0.0
        has_lines = len(items) > 0
        
        for item in items[:10]: # Max 10 lines
            # Name: Partial (Identity Protection)
            raw_name = xpath_first(item, './/ram:SpecifiedTradeProduct/ram:Name') or "Item"
            name = (raw_name[:15] + "...") if len(raw_name) > 15 else raw_name
            
            # Qty: Real
            raw_qty = xpath_first(item, './/ram:BilledQuantity')
            try:
                qty = float(raw_qty) if raw_qty else 1.0
            except:
                qty = 1.0
            
            # Unit Price: REAL (Unlocked for Developer Experience)
            raw_price = xpath_first(item, [
                './/ram:SpecifiedLineTradeAgreement/ram:NetPriceProductTradePrice/ram:ChargeAmount',
                './/ram:NetPriceProductTradePrice/ram:ChargeAmount',
                './/ram:GrossPriceProductTradePrice/ram:ChargeAmount'
            ])
            try:
                unit_price = float(raw_price) if raw_price else 0.0
            except:
                unit_price = 0.0
            
            # Line Total: REAL
            raw_line_total = xpath_first(item, [
                './/ram:SpecifiedLineTradeSettlement/ram:SpecifiedTradeSettlementLineMonetarySummation/ram:LineTotalAmount',
                './/ram:SpecifiedTradeSettlementMonetarySummation/ram:LineTotalAmount'
            ])
            try:
                line_total = float(raw_line_total) if raw_line_total else (qty * unit_price)
            except:
                line_total = qty * unit_price
            total_net += line_total
            
            # VAT Rate: REAL
            raw_vat = xpath_first(item, [
                './/ram:SpecifiedLineTradeSettlement/ram:ApplicableTradeTax/ram:RateApplicablePercent',
                './/ram:ApplicableTradeTax/ram:RateApplicablePercent'
            ])
            try:
                vat_rate = float(raw_vat) if raw_vat else 0.0
            except:
                vat_rate = 0.0
            
            line_items.append({
                "description": raw_name,  # Full name (no truncation in Open Core)
                "quantity": f"{qty}",
                "unit_code": xpath_first(item, './/ram:BilledQuantity/@unitCode') or "C62",
                "unit_price": f"{unit_price:.2f}",
                "vat_rate": f"{vat_rate:.2f}", 
                "line_total": f"{line_total:.2f}"
            })

        # 3. Totals: REAL (Unlocked for Developer Experience)
        # Extract real totals from XML
        raw_net = xpath_first(xml_root, [
            '//ram:ApplicableHeaderTradeSettlement/ram:SpecifiedTradeSettlementHeaderMonetarySummation/ram:TaxBasisTotalAmount',
            '//ram:SpecifiedTradeSettlementMonetarySummation/ram:TaxBasisTotalAmount',
            '//ram:SpecifiedTradeSettlementMonetarySummation/ram:LineTotalAmount'
        ])
        raw_tax = xpath_first(xml_root, [
            '//ram:ApplicableHeaderTradeSettlement/ram:SpecifiedTradeSettlementHeaderMonetarySummation/ram:TaxTotalAmount',
            '//ram:SpecifiedTradeSettlementMonetarySummation/ram:TaxTotalAmount'
        ])
        raw_gross = xpath_first(xml_root, [
            '//ram:ApplicableHeaderTradeSettlement/ram:SpecifiedTradeSettlementHeaderMonetarySummation/ram:GrandTotalAmount',
            '//ram:SpecifiedTradeSettlementMonetarySummation/ram:GrandTotalAmount'
        ])
        raw_payable = xpath_first(xml_root, [
            '//ram:ApplicableHeaderTradeSettlement/ram:SpecifiedTradeSettlementHeaderMonetarySummation/ram:DuePayableAmount',
            '//ram:SpecifiedTradeSettlementMonetarySummation/ram:DuePayableAmount'
        ])
        
        try:
            total_net_real = float(raw_net) if raw_net else total_net
        except:
            total_net_real = total_net
        try:
            tax_total = float(raw_tax) if raw_tax else 0.0
        except:
            tax_total = 0.0
        try:
            gross_total = float(raw_gross) if raw_gross else (total_net_real + tax_total)
        except:
            gross_total = total_net_real + tax_total
        try:
            payable_amount = float(raw_payable) if raw_payable else gross_total
        except:
            payable_amount = gross_total

        # 3. Extract REAL seller/buyer (Open Core Reset - no masking in Community)
        seller_name = xpath_first(xml_root, '//ram:SellerTradeParty/ram:Name') or ""
        seller_vat = xpath_first(xml_root, '//ram:SellerTradeParty//ram:SpecifiedTaxRegistration/ram:ID') or ""
        seller_address_line = xpath_first(xml_root, '//ram:SellerTradeParty/ram:PostalTradeAddress/ram:LineOne') or ""
        seller_city = xpath_first(xml_root, '//ram:SellerTradeParty/ram:PostalTradeAddress/ram:CityName') or ""
        seller_postcode = xpath_first(xml_root, '//ram:SellerTradeParty/ram:PostalTradeAddress/ram:PostcodeCode') or ""
        seller_country = xpath_first(xml_root, '//ram:SellerTradeParty/ram:PostalTradeAddress/ram:CountryID') or ""
        
        buyer_name = xpath_first(xml_root, '//ram:BuyerTradeParty/ram:Name') or ""
        buyer_vat = xpath_first(xml_root, '//ram:BuyerTradeParty//ram:SpecifiedTaxRegistration/ram:ID') or ""
        buyer_address_line = xpath_first(xml_root, '//ram:BuyerTradeParty/ram:PostalTradeAddress/ram:LineOne') or ""
        buyer_city = xpath_first(xml_root, '//ram:BuyerTradeParty/ram:PostalTradeAddress/ram:CityName') or ""
        buyer_postcode = xpath_first(xml_root, '//ram:BuyerTradeParty/ram:PostalTradeAddress/ram:PostcodeCode') or ""
        buyer_country = xpath_first(xml_root, '//ram:BuyerTradeParty/ram:PostalTradeAddress/ram:CountryID') or ""

        data = {
            "invoice_number": invoice_id,
            "invoice_date": date_str,
            "currency": currency,
            
            # Open Core: FULL identity exposed (no masking)
            "seller": {
                "name": seller_name,
                "vat_number": seller_vat,
                "address": {
                    "line": seller_address_line,
                    "city": seller_city,
                    "postal_code": seller_postcode,
                    "country": seller_country
                }
            },
            "buyer": {
                "name": buyer_name,
                "vat_number": buyer_vat,
                "address": {
                    "line": buyer_address_line,
                    "city": buyer_city,
                    "postal_code": buyer_postcode,
                    "country": buyer_country
                }
            },
            
            "totals": {
                "net_amount": f"{total_net_real:.2f}",
                "tax_amount": f"{tax_total:.2f}",
                "gross_amount": f"{gross_total:.2f}",
                "payable_amount": f"{payable_amount:.2f}"
            },
            
            "tax_breakdown": [
                {
                    "vat_rate": "REAL",  # TODO: Extract real breakdown
                    "tax_amount": f"{tax_total:.2f}",
                    "taxable_amount": f"{total_net_real:.2f}"
                }
            ],
            
            "line_items": line_items,
            
            "_meta": {
                "filename": filename,
                "edition": "community",  # Pro will add more fields
                "warnings": warnings if warnings else []
            }
        }
        
        return data
