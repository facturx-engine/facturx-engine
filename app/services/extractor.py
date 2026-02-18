"""
Extraction service for Community Edition (Open Core).
Parses Factur-X/ZUGFeRD XML and returns FULL invoice data (no obfuscation).
Pro edition adds advanced validation and compliance features.
"""
import logging
import asyncio
from io import BytesIO
from typing import Dict, Any
from lxml import etree
from app.services.pdf_utils import get_xml_from_pdf
from app.services.validation_utils import detect_format

logger = logging.getLogger(__name__)

class ExtractionService:
    """
    Community Edition Extractor.
    Parses Factur-X/ZUGFeRD and UBL (XRechnung) XML and generates a coherent DEMO invoice structure.
    """

    _SECURE_PARSER = etree.XMLParser(
        resolve_entities=False,
        no_network=True,
        huge_tree=False,
        recover=False  # Security: strict parsing
    )

    # Namespaces for UBL (Simplified for common XRechnung)
    NS_UBL = {
        'ubl': 'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2',
        'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
        'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'
    }

    @classmethod
    async def extract_invoice_data_async(cls, file_content: bytes, filename: str) -> Dict[str, Any]:
        """
        Asynchronous wrapper for extraction.
        Runs the blocking XML parsing in the default loop executor (ThreadPool).
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(
            None,  # Uses default ThreadPoolExecutor
            cls.extract_invoice_data,
            file_content,
            filename
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
            # 1. PDF Check & Extraction
            xml_bytes = None
            if filename.lower().endswith('.pdf') or file_content.startswith(b'%PDF'):
                try:
                    xml_filename, xml_bytes = get_xml_from_pdf(BytesIO(file_content), check_xsd=False)
                    if not xml_bytes:
                        result["format_detected"] = "not_facturx"
                        result["errors"].append({"code": "NO_XML", "message": "No Factur-X/ZUGFeRD/UBL XML found"})
                        return result
                    result["xml_extracted"] = True
                except Exception as e:
                    result["format_detected"] = "not_facturx"
                    result["errors"].append({"code": "EXTRACTION_FAIL", "message": f"PDF extraction failed: {str(e)}"})
                    return result
            else:
                # Assume raw XML
                xml_bytes = file_content
                result["xml_extracted"] = True

            # 2. Parse XML
            try:
                xml_root = etree.fromstring(xml_bytes, parser=ExtractionService._SECURE_PARSER)
                
                # Use shared detection logic
                fmt, profile = detect_format(xml_root)
                result["format_detected"] = fmt
                result["profile_detected"] = profile
                
                # 3. Map to Intelligent Demo JSON
                if fmt == "ubl":
                    result["invoice_json"] = ExtractionService._parse_demo_ubl(xml_root, filename)
                else:
                    # CII / Factur-X / ZUGFeRD
                    result["invoice_json"] = ExtractionService._parse_demo_cii(xml_root, fmt, filename)
                
            except Exception as e:
                result["errors"].append({"code": "PARSE_ERROR", "message": f"XML Parse error: {str(e)}"})
                logger.exception("Parse error")
                
            return result
            
        except Exception as e:
            logger.exception(f"Internal error: {e}")
            result["errors"].append({"code": "INTERNAL_ERROR", "message": str(e)})
            return result

    @staticmethod
    def _parse_demo_cii(xml_root, flavor, filename):
        # Existing CII parsing logic (renamed from _parse_demo_invoice)
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
            if isinstance(paths, str):
                paths = [paths]
            for p in paths:
                res = el.xpath(p, namespaces=ns)
                if res:
                    if hasattr(res[0], 'text'):
                        if res[0].text:
                            return res[0].text
                    else:
                        # It's already a string or text node
                        return str(res[0])
            return None

        # --- SMART DEMO MAPPING (CII) ---
        
        # 1. Structure (Real)
        invoice_id = xpath_first(xml_root, [
            '//rsm:ExchangedDocument/ram:ID', 
            '//rsm:HeaderExchangedDocument/ram:ID'
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
        
        for item in items[:20]: # Max 20 lines
            # Name
            raw_name = xpath_first(item, './/ram:SpecifiedTradeProduct/ram:Name') or "Item"
            
            # Qty
            raw_qty = xpath_first(item, './/ram:BilledQuantity')
            try:
                qty = float(raw_qty) if raw_qty else 1.0
            except Exception:
                qty = 1.0
            
            # Unit Price
            raw_price = xpath_first(item, [
                './/ram:SpecifiedLineTradeAgreement/ram:NetPriceProductTradePrice/ram:ChargeAmount',
                './/ram:NetPriceProductTradePrice/ram:ChargeAmount',
                './/ram:GrossPriceProductTradePrice/ram:ChargeAmount'
            ])
            try:
                unit_price = float(raw_price) if raw_price else 0.0
            except Exception:
                unit_price = 0.0
            
            # Line Total
            raw_line_total = xpath_first(item, [
                './/ram:SpecifiedTradeSettlement/ram:SpecifiedTradeSettlementLineMonetarySummation/ram:LineTotalAmount',
                './/ram:SpecifiedTradeSettlementMonetarySummation/ram:LineTotalAmount'
            ])
            try:
                line_total = float(raw_line_total) if raw_line_total else (qty * unit_price)
            except Exception:
                line_total = qty * unit_price
            total_net += line_total
            
            # VAT Rate
            raw_vat = xpath_first(item, [
                './/ram:SpecifiedTradeSettlement/ram:ApplicableTradeTax/ram:RateApplicablePercent',
                './/ram:ApplicableTradeTax/ram:RateApplicablePercent'
            ])
            try:
                vat_rate = float(raw_vat) if raw_vat else 0.0
            except Exception:
                vat_rate = 0.0
            
            line_items.append({
                "description": raw_name,
                "quantity": f"{qty}",
                "unit_code": xpath_first(item, './/ram:BilledQuantity/@unitCode') or "C62",
                "unit_price": f"{unit_price:.2f}",
                "vat_rate": f"{vat_rate:.2f}", 
                "line_total": f"{line_total:.2f}"
            })

        # 3. Totals
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
        except Exception:
            total_net_real = total_net
        try:
            tax_total = float(raw_tax) if raw_tax else 0.0
        except Exception:
            tax_total = 0.0
        try:
            gross_total = float(raw_gross) if raw_gross else (total_net_real + tax_total)
        except Exception:
            gross_total = total_net_real + tax_total
        try:
            payable_amount = float(raw_payable) if raw_payable else gross_total
        except Exception:
            payable_amount = gross_total

        # 4. Extract Seller/Buyer
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

        return {
            "invoice_number": invoice_id,
            "invoice_date": date_str,
            "currency": currency,
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
            "tax_breakdown": ExtractionService._parse_cii_tax_breakdown(xml_root, xpath_first, ns),
            "line_items": line_items,
            "_meta": {
                "filename": filename,
                "edition": "community",
                "warnings": warnings
            }
        }

    @staticmethod
    def _parse_demo_ubl(xml_root, filename):
        """Parse UBL XML into Demo JSON structure."""
        ns = ExtractionService.NS_UBL
        
        def xpath_first(el, path):
            res = el.xpath(path, namespaces=ns)
            if res:
                if hasattr(res[0], 'text'):
                    return res[0].text
                return str(res[0])
            return None

        # 1. Basic Info
        invoice_id = xpath_first(xml_root, '//cbc:ID')
        date_str = xpath_first(xml_root, '//cbc:IssueDate')
        currency = xpath_first(xml_root, '//cbc:DocumentCurrencyCode') or "EUR"

        # 2. Seller
        seller_node = xml_root.xpath('//cac:AccountingSupplierParty/cac:Party', namespaces=ns)
        seller = {"name": "", "vat_number": "", "address": {}}
        if seller_node:
            s_node = seller_node[0]
            seller["name"] = xpath_first(s_node, 'cac:PartyName/cbc:Name') or \
                             xpath_first(s_node, 'cac:PartyLegalEntity/cbc:RegistrationName') or ""
            seller["vat_number"] = xpath_first(s_node, 'cac:PartyTaxScheme/cbc:CompanyID') or ""
            seller["address"] = {
                "line": xpath_first(s_node, 'cac:PostalAddress/cbc:StreetName') or "",
                "city": xpath_first(s_node, 'cac:PostalAddress/cbc:CityName') or "",
                "postal_code": xpath_first(s_node, 'cac:PostalAddress/cbc:PostalZone') or "",
                "country": xpath_first(s_node, 'cac:PostalAddress/cac:Country/cbc:IdentificationCode') or ""
            }

        # 3. Buyer
        buyer_node = xml_root.xpath('//cac:AccountingCustomerParty/cac:Party', namespaces=ns)
        buyer = {"name": "", "vat_number": "", "address": {}}
        if buyer_node:
            b_node = buyer_node[0]
            buyer["name"] = xpath_first(b_node, 'cac:PartyName/cbc:Name') or \
                            xpath_first(b_node, 'cac:PartyLegalEntity/cbc:RegistrationName') or ""
            buyer["vat_number"] = xpath_first(b_node, 'cac:PartyTaxScheme/cbc:CompanyID') or ""
            buyer["address"] = {
                "line": xpath_first(b_node, 'cac:PostalAddress/cbc:StreetName') or "",
                "city": xpath_first(b_node, 'cac:PostalAddress/cbc:CityName') or "",
                "postal_code": xpath_first(b_node, 'cac:PostalAddress/cbc:PostalZone') or "",
                "country": xpath_first(b_node, 'cac:PostalAddress/cac:Country/cbc:IdentificationCode') or ""
            }

        # 4. Parsing Lines
        line_items = []
        lines_xml = xml_root.xpath('//cac:InvoiceLine', namespaces=ns)
        total_net_calc = 0.0

        for item in lines_xml[:50]:
            name = xpath_first(item, 'cac:Item/cbc:Name') or "Item"
            raw_qty = xpath_first(item, 'cbc:InvoicedQuantity')
            raw_price = xpath_first(item, 'cac:Price/cbc:PriceAmount')
            raw_total = xpath_first(item, 'cbc:LineExtensionAmount')
            raw_vat = xpath_first(item, 'cac:Item/cac:ClassifiedTaxCategory/cbc:Percent')
            
            qty = float(raw_qty) if raw_qty else 0.0
            price = float(raw_price) if raw_price else 0.0
            line_total = float(raw_total) if raw_total else (qty * price)
            vat_rate = float(raw_vat) if raw_vat else 0.0
            
            total_net_calc += line_total
            
            line_items.append({
                "description": name,
                "quantity": f"{qty}",
                "unit_code": xpath_first(item, 'cbc:InvoicedQuantity/@unitCode') or "C62",
                "unit_price": f"{price:.2f}",
                "vat_rate": f"{vat_rate:.2f}", 
                "line_total": f"{line_total:.2f}"
            })

        # 5. Totals
        raw_net = xpath_first(xml_root, '//cac:LegalMonetaryTotal/cbc:TaxExclusiveAmount')
        raw_tax = xpath_first(xml_root, '//cac:TaxTotal/cbc:TaxAmount')
        raw_gross = xpath_first(xml_root, '//cac:LegalMonetaryTotal/cbc:TaxInclusiveAmount')
        raw_payable = xpath_first(xml_root, '//cac:LegalMonetaryTotal/cbc:PayableAmount')

        net_val = float(raw_net) if raw_net else total_net_calc
        tax_val = float(raw_tax) if raw_tax else 0.0
        gross_val = float(raw_gross) if raw_gross else (net_val + tax_val)
        payable_val = float(raw_payable) if raw_payable else gross_val

        breakdown = []
        for subtotal in xml_root.xpath('//cac:TaxTotal/cac:TaxSubtotal', namespaces=ns):
            try:
                sub_rate = xpath_first(subtotal, 'cac:TaxCategory/cbc:Percent')
                sub_basis = xpath_first(subtotal, 'cbc:TaxableAmount')
                sub_amount = xpath_first(subtotal, 'cbc:TaxAmount')
                breakdown.append({
                    "category": xpath_first(subtotal, 'cac:TaxCategory/cbc:ID') or "S",
                    "vat_rate": f"{float(sub_rate) if sub_rate else 0:.2f}",
                    "basis_amount": f"{float(sub_basis) if sub_basis else 0:.2f}",
                    "tax_amount": f"{float(sub_amount) if sub_amount else 0:.2f}"
                })
            except Exception:
                pass

        return {
            "invoice_number": invoice_id,
            "invoice_date": date_str,
            "currency": currency,
            "seller": seller,
            "buyer": buyer,
            "totals": {
                "net_amount": f"{net_val:.2f}",
                "tax_amount": f"{tax_val:.2f}",
                "gross_amount": f"{gross_val:.2f}",
                "payable_amount": f"{payable_val:.2f}"
            },
            "tax_breakdown": breakdown,
            "line_items": line_items,
            "_meta": {
                "filename": filename,
                "edition": "community",
                "warnings": []
            }
        }

    @staticmethod
    def _parse_cii_tax_breakdown(xml_root, xpath_first, ns):
        """Parse ApplicableTradeTax elements into structured tax breakdown."""
        tax_nodes = xml_root.xpath(
            '//ram:ApplicableHeaderTradeSettlement/ram:ApplicableTradeTax',
            namespaces=ns
        )
        if not tax_nodes:
            # Fallback for older ZUGFeRD 1.x structure
            tax_nodes = xml_root.xpath('//ram:ApplicableTradeTax', namespaces=ns)

        breakdown = []
        for node in tax_nodes:
            category = xpath_first(node, 'ram:CategoryCode') or "S"
            rate = xpath_first(node, 'ram:RateApplicablePercent') or "0.00"
            basis = xpath_first(node, 'ram:BasisAmount') or "0.00"
            amount = xpath_first(node, 'ram:CalculatedAmount') or "0.00"

            try:
                breakdown.append({
                    "category": category,
                    "vat_rate": f"{float(rate):.2f}",
                    "basis_amount": f"{float(basis):.2f}",
                    "tax_amount": f"{float(amount):.2f}"
                })
            except (ValueError, TypeError) as e:
                logger.warning(f"Skipping malformed tax entry: {e}")

        return breakdown
