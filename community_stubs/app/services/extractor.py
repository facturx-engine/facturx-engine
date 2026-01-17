"""
Extraction service for Community Edition (Demo Mode).
Parses real XML but replaces sensitive financial values with coherent DEMO data.
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
                result["profile_detected"] = get_level(xml_root, result["format_detected"])
                
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
        invoice_id = xpath_first(xml_root, ['//ram:ID', '//rsm:HeaderExchangedDocument/ram:ID'])
        date_str = xpath_first(xml_root, ['//ram:IssueDateTime/udt:DateTimeString', '//rsm:HeaderExchangedDocument/ram:IssueDateTime/udt:DateTimeString'])
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
            # Name: Partial
            raw_name = xpath_first(item, './/ram:SpecifiedTradeProduct/ram:Name') or "Item"
            name = (raw_name[:15] + "...") if len(raw_name) > 15 else raw_name
            
            # Qty: Real
            raw_qty = xpath_first(item, './/ram:BilledQuantity')
            try:
                qty = float(raw_qty) if raw_qty else 1.0
            except:
                qty = 1.0
            
            # Unit Price: Fixed Demo Value
            unit_price = 100.00 
            
            # Line Total: Calculated
            line_total = qty * unit_price
            total_net += line_total
            
            line_items.append({
                "description": f"{name} [DEMO]",
                "quantity": qty,
                "unit_code": xpath_first(item, './/ram:BilledQuantity/@unitCode') or "C62",
                "unit_price": f"{unit_price:.2f}",
                "vat_rate": "20.00", 
                "line_total": f"{line_total:.2f}",
                "_demo": True
            })

        # 3. Totals
        # If we have lines, we sum them up (Coherent)
        # If no lines (Minimum), we use a Fixed Watermark on the extracted total or just 99.99
        
        if has_lines:
            tax_total = total_net * 0.20
            gross_total = total_net + tax_total
        else:
            # Minimum parsing: Extract real total if possible, but watermark it
            # For demo consistency, we force a recognizable pattern
            total_net = 1234.56
            tax_total = 246.91
            gross_total = 1481.47

        data = {
            "invoice_number": invoice_id,
            "invoice_date": date_str,
            "currency": currency,
            
            "seller": {
                "name": (xpath_first(xml_root, '//ram:SellerTradeParty/ram:Name') or "")[:5] + "****",
                "vat_number": "FRDEMO_INVALID_VAT",
                "address": "DEMO ADDRESS, 75000 PARIS"
            },
            "buyer": {
                "name": (xpath_first(xml_root, '//ram:BuyerTradeParty/ram:Name') or "")[:5] + "****"
            },
            
            "totals": {
                "net_amount": f"{total_net:.2f}",
                "tax_amount": f"{tax_total:.2f}",
                "gross_amount": f"{gross_total:.2f}",
                "payable_amount": f"{gross_total:.2f}",
                "_demo": True,
                "_watermark": "VALUES_ARE_DEMO_NOT_FOR_ACCOUNTING"
            },
            
            "tax_breakdown": [
                {
                    "vat_rate": "20.00",
                    "tax_amount": f"{tax_total:.2f}",
                    "taxable_amount": f"{total_net:.2f}",
                    "_demo": True
                }
            ],
            
            "line_items": line_items,
            
            "_meta": {
                "filename": filename,
                "demo_mode": True,
                "license_notice": "UNLICENSED_DEMO_OUTPUT_NOT_FOR_ACCOUNTING. Upgrade to Factur-X Engine Pro for full data.",
                "warnings": warnings if warnings else []
            },
            "_demo": {
               "policy": "2026-01-Smart-Obfuscation",
               "watermarked_fields": ["totals", "line_items.prices", "seller.vat"]
            }
        }
        
        return data
