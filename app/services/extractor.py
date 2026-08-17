"""Heuristic preview extraction for Factur-X/ZUGFeRD documents.

The output is useful for inspection but is never an automatic-import contract.
The strict normalized contract lives in ``BusinessReadySerializer``.
"""
import asyncio
import logging
from io import BytesIO
from typing import Any, Dict

from lxml import etree

from app.services.pdf_utils import get_xml_from_pdf
from app.services.validation_utils import detect_format

logger = logging.getLogger(__name__)

class ExtractionService:
    """
    Community Edition Extractor.
    Parses Factur-X/ZUGFeRD and UBL (XRechnung) XML and generates a coherent Community invoice structure.
    """

    _SECURE_PARSER = etree.XMLParser(
        resolve_entities=False,
        no_network=True,
        huge_tree=False,
        recover=False  # Security: strict parsing
    )

    # Namespaces for UBL Invoice (XRechnung, EN16931-UBL)
    NS_UBL = {
        'ubl': 'urn:oasis:names:specification:ubl:schema:xsd:Invoice-2',
        'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
        'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'
    }

    # Namespaces for UBL CreditNote (same CAC/CBC, different root namespace)
    NS_UBL_CN = {
        'cn': 'urn:oasis:names:specification:ubl:schema:xsd:CreditNote-2',
        'cac': 'urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2',
        'cbc': 'urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2'
    }

    # UBL root tags that identify document type
    _UBL_INVOICE_TAG = '{urn:oasis:names:specification:ubl:schema:xsd:Invoice-2}Invoice'
    _UBL_CREDITNOTE_TAG = '{urn:oasis:names:specification:ubl:schema:xsd:CreditNote-2}CreditNote'

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
                try:
                    if fmt == "ubl":
                        # Detect UBL document type: Invoice or CreditNote
                        root_tag = xml_root.tag
                        is_credit_note = root_tag == ExtractionService._UBL_CREDITNOTE_TAG
                        result["invoice_json"] = ExtractionService._parse_demo_ubl(
                            xml_root, filename, is_credit_note=is_credit_note
                        )
                    else:
                        result["invoice_json"] = ExtractionService._parse_demo_cii(xml_root, fmt or "factur-x", filename)
                except Exception as inner_e:
                    logger.error(f"INTELLIGENT PARSER FAIL: {str(inner_e)}")
                    raise inner_e # Re-raise to let outer catch handle or debug
                
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
        # Dynamic namespace selection based on detected Guideline ID (Profile)
        # EN16931-1 (including XRechnung 3.0) and Factur-X usually use the standard namespaces
        # Older ZUGFeRD 1.x use different URNs.

        # Standard CII (EN16931 / Factur-X)
        ns = {'rsm': 'urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100',
              'ram': 'urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100',
              'udt': 'urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100'}

        # Check if it might be an older flavor
        if flavor not in ('factur-x', 'facturx', 'ubl', 'xrechnung'):
             # Fallback check for root tag
             if 'CrossIndustryDocument' in xml_root.tag:
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
        limitations = ["heuristic_mapping"]
        fallback_values_used = False

        if len(items) > 20:
            limitations.append("max_20_lines_cii")

        if not items:
             limitations.append("missing_line_items")
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

        for item in items[:20]:  # Max 20 lines
            # Name
            raw_name_value = xpath_first(item, './/ram:SpecifiedTradeProduct/ram:Name')
            raw_name = raw_name_value or "Item"
            if not raw_name_value:
                fallback_values_used = True

            # Qty
            raw_qty = xpath_first(item, './/ram:BilledQuantity')
            try:
                qty = float(raw_qty) if raw_qty else 1.0
                if not raw_qty:
                    fallback_values_used = True
            except Exception:
                qty = 1.0
                fallback_values_used = True

            # Unit Price
            raw_price = xpath_first(item, [
                './/ram:SpecifiedLineTradeAgreement/ram:NetPriceProductTradePrice/ram:ChargeAmount',
                './/ram:NetPriceProductTradePrice/ram:ChargeAmount',
                './/ram:GrossPriceProductTradePrice/ram:ChargeAmount'
            ])
            try:
                unit_price = float(raw_price) if raw_price else 0.0
                if not raw_price:
                    fallback_values_used = True
            except Exception:
                unit_price = 0.0
                fallback_values_used = True

            # Line Total
            raw_line_total = xpath_first(item, [
                './/ram:SpecifiedLineTradeSettlement/ram:SpecifiedTradeSettlementLineMonetarySummation/ram:LineTotalAmount',
                './/ram:SpecifiedTradeSettlementMonetarySummation/ram:LineTotalAmount'
            ])
            try:
                line_total = float(raw_line_total) if raw_line_total else (qty * unit_price)
                if not raw_line_total:
                    fallback_values_used = True
            except Exception:
                line_total = qty * unit_price
                fallback_values_used = True
            total_net += line_total

            # VAT Rate
            raw_vat = xpath_first(item, [
                './/ram:SpecifiedLineTradeSettlement/ram:ApplicableTradeTax/ram:RateApplicablePercent',
                './/ram:ApplicableTradeTax/ram:RateApplicablePercent'
            ])
            try:
                vat_rate = float(raw_vat) if raw_vat else 0.0
                if not raw_vat:
                    fallback_values_used = True
            except Exception:
                vat_rate = 0.0
                fallback_values_used = True

            unit_code_raw = xpath_first(item, './/ram:BilledQuantity/@unitCode')
            if not unit_code_raw:
                fallback_values_used = True

            line_items.append({
                "description": raw_name,
                "quantity": f"{qty}",
                "unit_code": unit_code_raw or "C62",
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
            if not raw_net:
                fallback_values_used = True
        except Exception:
            total_net_real = total_net
            fallback_values_used = True
        try:
            tax_total = float(raw_tax) if raw_tax else 0.0
            if not raw_tax:
                fallback_values_used = True
        except Exception:
            tax_total = 0.0
            fallback_values_used = True
        try:
            gross_total = float(raw_gross) if raw_gross else (total_net_real + tax_total)
            if not raw_gross:
                fallback_values_used = True
        except Exception:
            gross_total = total_net_real + tax_total
            fallback_values_used = True
        try:
            payable_amount = float(raw_payable) if raw_payable else gross_total
            if not raw_payable:
                fallback_values_used = True
        except Exception:
            payable_amount = gross_total
            fallback_values_used = True

        if fallback_values_used:
            limitations.append("fallback_values_used")

        # 4. Extract Seller/Buyer & Secondary Header Info
        due_date = xpath_first(xml_root, '//ram:ApplicableHeaderTradeSettlement/ram:SpecifiedTradePaymentTerms/ram:DueDateDateTime/udt:DateTimeString')

        def clean_str(s):
            return s if s and s.strip() else None

        seller_name = xpath_first(xml_root, '//ram:SellerTradeParty/ram:Name') or ""
        seller_vat = xpath_first(xml_root, '//ram:SellerTradeParty//ram:SpecifiedTaxRegistration/ram:ID') or ""
        seller_reg = xpath_first(xml_root, '//ram:SellerTradeParty/ram:SpecifiedLegalOrganization/ram:ID')
        seller_email = xpath_first(xml_root, '//ram:SellerTradeParty/ram:DefinedTradeContact/ram:EmailURIUniversalCommunication/ram:URIID')

        seller_address_line = clean_str(xpath_first(xml_root, '//ram:SellerTradeParty/ram:PostalTradeAddress/ram:LineOne'))
        seller_city = clean_str(xpath_first(xml_root, '//ram:SellerTradeParty/ram:PostalTradeAddress/ram:CityName'))
        seller_postcode = clean_str(xpath_first(xml_root, '//ram:SellerTradeParty/ram:PostalTradeAddress/ram:PostcodeCode'))
        seller_country = clean_str(xpath_first(xml_root, '//ram:SellerTradeParty/ram:PostalTradeAddress/ram:CountryID'))

        buyer_name = xpath_first(xml_root, '//ram:BuyerTradeParty/ram:Name') or ""
        buyer_vat = xpath_first(xml_root, '//ram:BuyerTradeParty//ram:SpecifiedTaxRegistration/ram:ID') or ""
        buyer_reg = xpath_first(xml_root, '//ram:BuyerTradeParty/ram:SpecifiedLegalOrganization/ram:ID')
        buyer_email = xpath_first(xml_root, '//ram:BuyerTradeParty/ram:DefinedTradeContact/ram:EmailURIUniversalCommunication/ram:URIID')

        buyer_address_line = clean_str(xpath_first(xml_root, '//ram:BuyerTradeParty/ram:PostalTradeAddress/ram:LineOne'))
        buyer_city = clean_str(xpath_first(xml_root, '//ram:BuyerTradeParty/ram:PostalTradeAddress/ram:CityName'))
        buyer_postcode = clean_str(xpath_first(xml_root, '//ram:BuyerTradeParty/ram:PostalTradeAddress/ram:PostcodeCode'))
        buyer_country = clean_str(xpath_first(xml_root, '//ram:BuyerTradeParty/ram:PostalTradeAddress/ram:CountryID'))

        return {
            "invoice_number": invoice_id,
            "invoice_date": date_str,
            "due_date": due_date,
            "currency": currency,
            "buyer_reference": xpath_first(xml_root, '//ram:ApplicableHeaderTradeAgreement/ram:BuyerReference'),
            "contract_reference": xpath_first(xml_root, '//ram:ApplicableHeaderTradeAgreement/ram:ContractReferencedDocument/ram:IssuerAssignedID'),
            "seller": {
                "name": seller_name,
                "registration_id": seller_reg,
                "email": seller_email,
                "vat_number": seller_vat,
                "line1": seller_address_line,
                "city": seller_city,
                "postcode": seller_postcode,
                "country": seller_country
            },
            "buyer": {
                "name": buyer_name,
                "registration_id": buyer_reg,
                "email": buyer_email,
                "vat_number": buyer_vat,
                "line1": buyer_address_line,
                "city": buyer_city,
                "postcode": buyer_postcode,
                "country": buyer_country
            },
            "tax_breakdown": ExtractionService._parse_cii_tax_breakdown(xml_root, xpath_first, ns),
            "totals": {
                "net_amount": f"{total_net_real:.2f}",
                "tax_amount": f"{tax_total:.2f}",
                "gross_amount": f"{gross_total:.2f}",
                "payable_amount": f"{payable_amount:.2f}"
            },
            "line_items": line_items,
            "_meta": {
                "filename": filename,
                "edition": "community",
                "warnings": warnings,
                "limitations": limitations,
            }
        }

    @staticmethod
    def _parse_demo_ubl(xml_root, filename, is_credit_note: bool = False):
        """Parse UBL Invoice or CreditNote XML into Demo JSON structure.

        UBL CreditNote uses the same CAC/CBC namespaces as Invoice but:
          - root namespace is CreditNote-2 instead of Invoice-2
          - line elements are <cac:CreditNoteLine> with <cbc:CreditedQuantity>
          - there is no <cbc:DueDate> (credit notes don't have payment terms)
          - document_type is reported as "credit_note" in _meta
        """
        # Select namespace set based on document type
        ns = ExtractionService.NS_UBL_CN if is_credit_note else ExtractionService.NS_UBL
        document_type = "credit_note" if is_credit_note else "invoice"

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
        # CreditNote has no DueDate; Invoice may have one
        due_date = xpath_first(xml_root, '//cbc:DueDate') if not is_credit_note else None
        # CreditNote may carry a TaxPointDate instead
        tax_point_date = xpath_first(xml_root, '//cbc:TaxPointDate') if is_credit_note else None
        currency = xpath_first(xml_root, '//cbc:DocumentCurrencyCode') or "EUR"
        # BillingReference: the original invoice number a credit note refers to
        billing_ref = xpath_first(xml_root, '//cac:BillingReference/cac:InvoiceDocumentReference/cbc:ID')             if is_credit_note else None

        def clean_str(s):
            return s if s and s.strip() else None

        # 2. Seller (AccountingSupplierParty ? identical in both document types)
        seller_node = xml_root.xpath('//cac:AccountingSupplierParty/cac:Party', namespaces=ns)
        seller = {"name": "", "vat_number": "", "registration_id": None, "email": None}
        if seller_node:
            s_node = seller_node[0]
            seller["name"] = xpath_first(s_node, 'cac:PartyName/cbc:Name') or                              xpath_first(s_node, 'cac:PartyLegalEntity/cbc:RegistrationName') or ""
            seller["vat_number"] = xpath_first(s_node, 'cac:PartyTaxScheme/cbc:CompanyID') or ""
            seller["registration_id"] = xpath_first(s_node, 'cac:PartyLegalEntity/cbc:CompanyID')
            seller["email"] = xpath_first(s_node, 'cac:Contact/cbc:ElectronicMail')
            seller["line1"] = clean_str(xpath_first(s_node, 'cac:PostalAddress/cbc:StreetName'))
            seller["city"] = clean_str(xpath_first(s_node, 'cac:PostalAddress/cbc:CityName'))
            seller["postcode"] = clean_str(xpath_first(s_node, 'cac:PostalAddress/cbc:PostalZone'))
            seller["country"] = clean_str(xpath_first(s_node, 'cac:PostalAddress/cac:Country/cbc:IdentificationCode'))

        # 3. Buyer (AccountingCustomerParty ? identical in both document types)
        buyer_node = xml_root.xpath('//cac:AccountingCustomerParty/cac:Party', namespaces=ns)
        buyer = {"name": "", "vat_number": "", "registration_id": None, "email": None}
        if buyer_node:
            b_node = buyer_node[0]
            buyer["name"] = xpath_first(b_node, 'cac:PartyName/cbc:Name') or                             xpath_first(b_node, 'cac:PartyLegalEntity/cbc:RegistrationName') or ""
            buyer["vat_number"] = xpath_first(b_node, 'cac:PartyTaxScheme/cbc:CompanyID') or ""
            buyer["registration_id"] = xpath_first(b_node, 'cac:PartyLegalEntity/cbc:CompanyID')
            buyer["email"] = xpath_first(b_node, 'cac:Contact/cbc:ElectronicMail')
            buyer["line1"] = clean_str(xpath_first(b_node, 'cac:PostalAddress/cbc:StreetName'))
            buyer["city"] = clean_str(xpath_first(b_node, 'cac:PostalAddress/cbc:CityName'))
            buyer["postcode"] = clean_str(xpath_first(b_node, 'cac:PostalAddress/cbc:PostalZone'))
            buyer["country"] = clean_str(xpath_first(b_node, 'cac:PostalAddress/cac:Country/cbc:IdentificationCode'))

        # 4. Line Items
        # Invoice uses <cac:InvoiceLine> / <cbc:InvoicedQuantity>
        # CreditNote uses <cac:CreditNoteLine> / <cbc:CreditedQuantity>
        line_items = []
        total_net_calc = 0.0
        limitations = ["heuristic_mapping"]
        fallback_values_used = False

        if is_credit_note:
            lines_xml = xml_root.xpath('//cac:CreditNoteLine', namespaces=ns)
            qty_tag = 'cbc:CreditedQuantity'
        else:
            lines_xml = xml_root.xpath('//cac:InvoiceLine', namespaces=ns)
            qty_tag = 'cbc:InvoicedQuantity'

        if not lines_xml:
            limitations.append("missing_line_items")

        for item in lines_xml[:50]:
            raw_name = xpath_first(item, 'cac:Item/cbc:Name')
            name = raw_name or "Item"
            if not raw_name:
                fallback_values_used = True

            raw_qty = xpath_first(item, qty_tag)
            raw_price = xpath_first(item, 'cac:Price/cbc:PriceAmount')
            raw_total = xpath_first(item, 'cbc:LineExtensionAmount')
            raw_vat = xpath_first(item, 'cac:Item/cac:ClassifiedTaxCategory/cbc:Percent')

            try:
                qty = float(raw_qty) if raw_qty else 0.0
                if not raw_qty:
                    fallback_values_used = True
            except Exception:
                qty = 0.0
                fallback_values_used = True

            try:
                price = float(raw_price) if raw_price else 0.0
                if not raw_price:
                    fallback_values_used = True
            except Exception:
                price = 0.0
                fallback_values_used = True

            try:
                line_total = float(raw_total) if raw_total else (qty * price)
                if not raw_total:
                    fallback_values_used = True
            except Exception:
                line_total = qty * price
                fallback_values_used = True

            try:
                vat_rate = float(raw_vat) if raw_vat else 0.0
                if not raw_vat:
                    fallback_values_used = True
            except Exception:
                vat_rate = 0.0
                fallback_values_used = True

            total_net_calc += line_total

            unit_code = xpath_first(item, f'{qty_tag}/@unitCode')
            if not unit_code:
                fallback_values_used = True

            line_items.append({
                "description": name,
                "quantity": f"{qty}",
                "unit_code": unit_code or "C62",
                "unit_price": f"{price:.2f}",
                "vat_rate": f"{vat_rate:.2f}",
                "line_total": f"{line_total:.2f}"
            })

        # 5. Totals (LegalMonetaryTotal is identical in both document types)
        raw_net = xpath_first(xml_root, '//cac:LegalMonetaryTotal/cbc:TaxExclusiveAmount')
        raw_tax = xpath_first(xml_root, '//cac:TaxTotal/cbc:TaxAmount')
        raw_gross = xpath_first(xml_root, '//cac:LegalMonetaryTotal/cbc:TaxInclusiveAmount')
        raw_payable = xpath_first(xml_root, '//cac:LegalMonetaryTotal/cbc:PayableAmount')

        try:
            net_val = float(raw_net) if raw_net else total_net_calc
            if not raw_net:
                fallback_values_used = True
        except Exception:
            net_val = total_net_calc
            fallback_values_used = True

        try:
            tax_val = float(raw_tax) if raw_tax else 0.0
            if not raw_tax:
                fallback_values_used = True
        except Exception:
            tax_val = 0.0
            fallback_values_used = True

        try:
            gross_val = float(raw_gross) if raw_gross else (net_val + tax_val)
            if not raw_gross:
                fallback_values_used = True
        except Exception:
            gross_val = net_val + tax_val
            fallback_values_used = True

        try:
            payable_val = float(raw_payable) if raw_payable else gross_val
            if not raw_payable:
                fallback_values_used = True
        except Exception:
            payable_val = gross_val
            fallback_values_used = True

        # 6. Tax Breakdown (identical structure in both document types)
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

        if fallback_values_used:
            limitations.append("fallback_values_used")

        # 7. Build output dict
        warnings = []
        if is_credit_note and not billing_ref:
            warnings.append({
                "code": "NO_BILLING_REFERENCE",
                "message": "CreditNote: no BillingReference/InvoiceDocumentReference found."
            })

        result = {
            "invoice_number": invoice_id,
            "invoice_date": date_str,
            "currency": currency,
            "buyer_reference": xpath_first(xml_root, '//cbc:BuyerReference'),
            "contract_reference": xpath_first(xml_root, '//cac:ContractDocumentReference/cbc:ID'),
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
                "document_type": document_type,
                "warnings": warnings,
                "limitations": limitations,
            }
        }

        # Add document-type-specific fields
        if is_credit_note:
            result["billing_reference"] = billing_ref
            result["tax_point_date"] = tax_point_date
        else:
            result["due_date"] = due_date

        return result

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
