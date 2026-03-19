"""
Business-Ready JSON Serializer.
Transitions from XML (CII/UBL) to a normalized, high-precision JSON format.
Pro Feature: Supports UBL, CII, and automatic field translation.
"""
import logging
from datetime import date, datetime
from decimal import Decimal
from typing import Any, Dict, List, Tuple

from lxml import etree

from app.schemas.integration import (
    AddressSchema,
    BusinessReadyInvoice,
    LineItemSchema,
    PartySchema,
    TaxBreakdownSchema,
)
from app.services.validation_utils import detect_format

logger = logging.getLogger(__name__)


class BusinessReadySerializer:
    """
    Transforms Factur-X/ZUGFeRD/XRechnung XML into the Pro Business-Ready format.

    Supports:
    - CII (Cross Industry Invoice) - Factur-X / ZUGFeRD
    - UBL (Universal Business Language) - XRechnung / Peppol
    """

    # Namespaces for CII
    NS_CII = {
        "rsm": "urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100",
        "ram": "urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100",
        "udt": "urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100",
    }

    # Namespaces for UBL (Simplified for common XRechnung)
    NS_UBL = {
        "ubl": "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2",
        "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
        "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
    }

    @staticmethod
    def _record_fallback(
        fallbacks: List[Dict[str, Any]],
        field: str,
        fallback_type: str,
        original_state: str,
        applied_value: Any,
    ) -> None:
        fallbacks.append(
            {
                "field": field,
                "fallback_type": fallback_type,
                "original_state": original_state,
                "applied_value": applied_value,
            }
        )

    @staticmethod
    def _decimal_or_default(raw_value: Any, field: str, fallbacks: List[Dict[str, Any]]) -> Decimal:
        if raw_value is None or str(raw_value).strip() == "":
            BusinessReadySerializer._record_fallback(
                fallbacks, field, "default_value", "missing", "0"
            )
            return Decimal("0")
        try:
            return Decimal(str(raw_value))
        except Exception:
            BusinessReadySerializer._record_fallback(
                fallbacks, field, "coercion", "invalid", "0"
            )
            return Decimal("0")

    @staticmethod
    def serialize(xml_bytes: bytes, is_pro: bool = False) -> BusinessReadyInvoice:
        """
        Backward-compatible entry point: returns only the invoice payload.
        """
        invoice, _, _ = BusinessReadySerializer.serialize_with_diagnostics(xml_bytes, is_pro=is_pro)
        return invoice

    @staticmethod
    def serialize_with_diagnostics(
        xml_bytes: bytes, is_pro: bool = False
    ) -> Tuple[BusinessReadyInvoice, List[Dict[str, Any]], bool]:
        """
        Main serialization entry point with fallback diagnostics.

        Returns:
            (invoice, fallbacks_applied, xml_recovery_applied)
        """
        fallbacks: List[Dict[str, Any]] = []

        parser = etree.XMLParser(recover=True, resolve_entities=False, no_network=True)
        root = etree.fromstring(xml_bytes, parser=parser)

        xml_recovery_applied = len(parser.error_log) > 0
        if xml_recovery_applied:
            BusinessReadySerializer._record_fallback(
                fallbacks,
                "invoice",
                "xml_parser_recovery",
                "malformed",
                None,
            )

        if "CrossIndustryInvoice" in root.tag:
            invoice = BusinessReadySerializer._parse_cii(root, fallbacks)
        elif "Invoice" in root.tag and "urn:oasis:names:specification:ubl" in root.tag:
            invoice = BusinessReadySerializer._parse_ubl(root, fallbacks)
        else:
            raise ValueError("Unsupported XML format. Must be CII (Factur-X) or UBL.")

        return invoice, fallbacks, xml_recovery_applied

    @staticmethod
    def _parse_cii(root: etree._Element, fallbacks: List[Dict[str, Any]]) -> BusinessReadyInvoice:
        """Parse CII XML (Factur-X / ZUGFeRD)."""
        ns = BusinessReadySerializer.NS_CII

        def xpath_first(el: etree._Element, path: str) -> str | None:
            res = el.xpath(path, namespaces=ns)
            return res[0].text if res and hasattr(res[0], "text") and res[0].text else None

        inv_id = xpath_first(root, "//rsm:ExchangedDocument/ram:ID")
        invoice_number = inv_id or "UNKNOWN"
        if not inv_id:
            BusinessReadySerializer._record_fallback(
                fallbacks,
                "invoice.invoice_number",
                "placeholder_value",
                "missing",
                "UNKNOWN",
            )

        date_str = xpath_first(root, "//rsm:ExchangedDocument/ram:IssueDateTime/udt:DateTimeString")
        try:
            inv_date = datetime.strptime(date_str, "%Y%m%d").date()  # type: ignore[arg-type]
        except (ValueError, TypeError):
            inv_date = date.today()
            BusinessReadySerializer._record_fallback(
                fallbacks,
                "invoice.invoice_date",
                "default_value",
                "missing" if date_str is None else "invalid",
                inv_date.isoformat(),
            )

        seller_nodes = root.xpath("//ram:SellerTradeParty", namespaces=ns)
        if not seller_nodes:
            raise ValueError("Invalid CII: Missing SellerTradeParty (mandatory)")
        seller = BusinessReadySerializer._parse_cii_party(
            seller_nodes[0], fallbacks, "invoice.seller"
        )

        buyer_nodes = root.xpath("//ram:BuyerTradeParty", namespaces=ns)
        if not buyer_nodes:
            raise ValueError("Invalid CII: Missing BuyerTradeParty (mandatory)")
        buyer = BusinessReadySerializer._parse_cii_party(
            buyer_nodes[0], fallbacks, "invoice.buyer"
        )

        due_date_str = xpath_first(
            root,
            "//ram:ApplicableHeaderTradeSettlement/ram:SpecifiedTradePaymentTerms/ram:DueDateDateTime/udt:DateTimeString",
        )
        due_date = None
        if due_date_str:
            try:
                due_date = datetime.strptime(due_date_str, "%Y%m%d").date()
            except Exception:
                due_date = None

        line_items: List[LineItemSchema] = []
        for idx, line_node in enumerate(
            root.xpath("//ram:IncludedSupplyChainTradeLineItem", namespaces=ns)
        ):
            try:
                line_items.append(
                    BusinessReadySerializer._parse_cii_line(line_node, fallbacks, idx)
                )
            except (IndexError, KeyError, ValueError) as e:
                logger.warning(f"Skipping malformed line item: {e}")
                BusinessReadySerializer._record_fallback(
                    fallbacks,
                    f"invoice.line_items[{idx}]",
                    "line_skipped",
                    "malformed",
                    None,
                )

        fmt, profile = detect_format(root)
        output_format = fmt or "factur-x"
        output_profile = profile or "en16931"
        if not fmt:
            BusinessReadySerializer._record_fallback(
                fallbacks,
                "invoice.format",
                "default_value",
                "missing",
                "factur-x",
            )
        if not profile:
            BusinessReadySerializer._record_fallback(
                fallbacks,
                "invoice.profile",
                "default_value",
                "missing",
                "en16931",
            )

        raw_currency = xpath_first(root, "//ram:InvoiceCurrencyCode")
        currency = raw_currency or "EUR"
        if not raw_currency:
            BusinessReadySerializer._record_fallback(
                fallbacks,
                "invoice.currency",
                "default_value",
                "missing",
                "EUR",
            )

        summation_nodes = root.xpath(
            "//ram:SpecifiedTradeSettlementHeaderMonetarySummation", namespaces=ns
        )
        if not summation_nodes:
            raise ValueError("Invalid CII: Missing MonetarySummation (mandatory)")
        summation_node = summation_nodes[0]

        return BusinessReadyInvoice(
            invoice_number=invoice_number,
            invoice_date=inv_date,
            due_date=due_date,
            format=output_format,
            profile=output_profile,
            currency=currency,
            buyer_reference=xpath_first(
                root, "//ram:ApplicableHeaderTradeAgreement/ram:BuyerReference"
            ),
            contract_reference=xpath_first(
                root,
                "//ram:ApplicableHeaderTradeAgreement/ram:ContractReferencedDocument/ram:IssuerAssignedID",
            ),
            seller=seller,
            buyer=buyer,
            line_items=line_items,
            tax_breakdown=BusinessReadySerializer._parse_cii_tax_breakdown(root),
            total_net_amount=BusinessReadySerializer._decimal_or_default(
                xpath_first(summation_node, "ram:TaxBasisTotalAmount"),
                "invoice.total_net_amount",
                fallbacks,
            ),
            total_tax_amount=BusinessReadySerializer._decimal_or_default(
                xpath_first(summation_node, "ram:TaxTotalAmount"),
                "invoice.total_tax_amount",
                fallbacks,
            ),
            total_gross_amount=BusinessReadySerializer._decimal_or_default(
                xpath_first(summation_node, "ram:GrandTotalAmount"),
                "invoice.total_gross_amount",
                fallbacks,
            ),
            amount_due=BusinessReadySerializer._decimal_or_default(
                xpath_first(summation_node, "ram:DuePayableAmount"),
                "invoice.amount_due",
                fallbacks,
            ),
        )

    @staticmethod
    def _parse_cii_party(
        node: etree._Element, fallbacks: List[Dict[str, Any]], party_prefix: str
    ) -> PartySchema:
        ns = BusinessReadySerializer.NS_CII

        def get_text(xpath: str) -> str | None:
            res = node.xpath(xpath, namespaces=ns)
            return res[0].text if res and hasattr(res[0], "text") and res[0].text else None

        raw_name = get_text("ram:Name")
        name = raw_name or "Unknown"
        if not raw_name:
            BusinessReadySerializer._record_fallback(
                fallbacks,
                f"{party_prefix}.name",
                "placeholder_value",
                "missing",
                "Unknown",
            )

        line1 = get_text(".//ram:PostalTradeAddress/ram:LineOne") or "..."
        if line1 == "...":
            BusinessReadySerializer._record_fallback(
                fallbacks,
                f"{party_prefix}.address.line1",
                "placeholder_value",
                "missing",
                "...",
            )

        city = get_text(".//ram:PostalTradeAddress/ram:CityName") or "..."
        if city == "...":
            BusinessReadySerializer._record_fallback(
                fallbacks,
                f"{party_prefix}.address.city",
                "placeholder_value",
                "missing",
                "...",
            )

        postcode = get_text(".//ram:PostalTradeAddress/ram:PostcodeCode") or "..."
        if postcode == "...":
            BusinessReadySerializer._record_fallback(
                fallbacks,
                f"{party_prefix}.address.postcode",
                "placeholder_value",
                "missing",
                "...",
            )

        country_code = get_text(".//ram:PostalTradeAddress/ram:CountryID") or "FR"
        if country_code == "FR" and not get_text(".//ram:PostalTradeAddress/ram:CountryID"):
            BusinessReadySerializer._record_fallback(
                fallbacks,
                f"{party_prefix}.address.country_code",
                "default_value",
                "missing",
                "FR",
            )

        return PartySchema(
            name=name,
            vat_number=get_text(".//ram:SpecifiedTaxRegistration/ram:ID"),
            registration_id=get_text("ram:SpecifiedLegalOrganization/ram:ID"),
            email=get_text("ram:DefinedTradeContact/ram:EmailURIUniversalCommunication/ram:URIID"),
            address=AddressSchema(
                line1=line1,
                city=city,
                postcode=postcode,
                country_code=country_code,
            ),
        )

    @staticmethod
    def _parse_cii_line(
        node: etree._Element, fallbacks: List[Dict[str, Any]], line_index: int
    ) -> LineItemSchema:
        ns = BusinessReadySerializer.NS_CII

        name = node.xpath(".//ram:SpecifiedTradeProduct/ram:Name/text()", namespaces=ns)[0]
        qty = Decimal(node.xpath(".//ram:BilledQuantity/text()", namespaces=ns)[0] or "1")
        price = Decimal(
            node.xpath(".//ram:NetPriceProductTradePrice/ram:ChargeAmount/text()", namespaces=ns)[0]
            or "0"
        )
        total = Decimal(
            node.xpath(
                ".//ram:SpecifiedTradeSettlementLineMonetarySummation/ram:LineTotalAmount/text()",
                namespaces=ns,
            )[0]
            or "0"
        )

        unit_code_candidates = node.xpath(".//ram:BilledQuantity/@unitCode", namespaces=ns)
        unit_code = unit_code_candidates[0] if unit_code_candidates else "C62"
        if not unit_code_candidates:
            BusinessReadySerializer._record_fallback(
                fallbacks,
                f"invoice.line_items[{line_index}].unit_code",
                "default_value",
                "missing",
                "C62",
            )

        vat_rate_raw = node.xpath(
            ".//ram:ApplicableTradeTax/ram:RateApplicablePercent/text()", namespaces=ns
        )[0]
        vat_rate = Decimal(vat_rate_raw or "0")

        return LineItemSchema(
            name=name,
            quantity=qty,
            unit_code=unit_code,
            net_price=price,
            line_total=total,
            vat_rate=vat_rate,
        )

    @staticmethod
    def _parse_cii_tax_breakdown(root: etree._Element) -> list:
        """Parse ApplicableTradeTax elements into TaxBreakdownSchema list."""
        ns = BusinessReadySerializer.NS_CII

        def xpath_text(el: etree._Element, path: str) -> str | None:
            res = el.xpath(path + "/text()", namespaces=ns)
            return res[0] if res else None

        tax_nodes = root.xpath(
            "//ram:ApplicableHeaderTradeSettlement/ram:ApplicableTradeTax",
            namespaces=ns,
        )
        if not tax_nodes:
            tax_nodes = root.xpath("//ram:ApplicableTradeTax", namespaces=ns)

        breakdown = []
        for node in tax_nodes:
            try:
                breakdown.append(
                    TaxBreakdownSchema(
                        category=xpath_text(node, "ram:CategoryCode") or "S",
                        rate=Decimal(xpath_text(node, "ram:RateApplicablePercent") or "0"),
                        basis_amount=Decimal(xpath_text(node, "ram:BasisAmount") or "0"),
                        tax_amount=Decimal(xpath_text(node, "ram:CalculatedAmount") or "0"),
                    )
                )
            except Exception as e:
                logger.warning(f"Skipping malformed tax entry: {e}")

        return breakdown

    @staticmethod
    def _parse_ubl(root: etree._Element, fallbacks: List[Dict[str, Any]]) -> BusinessReadyInvoice:
        """Parse UBL XML (XRechnung / Peppol)."""
        ns = BusinessReadySerializer.NS_UBL

        def xpath_first(el: etree._Element, path: str) -> str | None:
            res = el.xpath(path, namespaces=ns)
            return res[0].text if res and hasattr(res[0], "text") and res[0].text else None

        inv_id = xpath_first(root, "//cbc:ID")
        invoice_number = inv_id or "UNKNOWN"
        if not inv_id:
            BusinessReadySerializer._record_fallback(
                fallbacks,
                "invoice.invoice_number",
                "placeholder_value",
                "missing",
                "UNKNOWN",
            )

        date_str = xpath_first(root, "//cbc:IssueDate")
        try:
            inv_date = datetime.strptime(date_str, "%Y-%m-%d").date()  # type: ignore[arg-type]
        except (ValueError, TypeError):
            inv_date = date.today()
            BusinessReadySerializer._record_fallback(
                fallbacks,
                "invoice.invoice_date",
                "default_value",
                "missing" if date_str is None else "invalid",
                inv_date.isoformat(),
            )

        due_date_str = xpath_first(root, "//cbc:DueDate")
        due_date = None
        if due_date_str:
            try:
                due_date = datetime.strptime(due_date_str, "%Y-%m-%d").date()
            except Exception:
                due_date = None

        seller_nodes = root.xpath("//cac:AccountingSupplierParty/cac:Party", namespaces=ns)
        if not seller_nodes:
            raise ValueError("Invalid UBL: Missing AccountingSupplierParty (mandatory)")
        seller = BusinessReadySerializer._parse_ubl_party(
            seller_nodes[0], fallbacks, "invoice.seller"
        )

        buyer_nodes = root.xpath("//cac:AccountingCustomerParty/cac:Party", namespaces=ns)
        if not buyer_nodes:
            raise ValueError("Invalid UBL: Missing AccountingCustomerParty (mandatory)")
        buyer = BusinessReadySerializer._parse_ubl_party(
            buyer_nodes[0], fallbacks, "invoice.buyer"
        )

        line_items: List[LineItemSchema] = []
        for idx, line_node in enumerate(root.xpath("//cac:InvoiceLine", namespaces=ns)):
            try:
                line_items.append(
                    BusinessReadySerializer._parse_ubl_line(line_node, fallbacks, idx)
                )
            except (IndexError, KeyError, ValueError) as e:
                logger.warning(f"Skipping malformed UBL line item: {e}")
                BusinessReadySerializer._record_fallback(
                    fallbacks,
                    f"invoice.line_items[{idx}]",
                    "line_skipped",
                    "malformed",
                    None,
                )

        legal_monetary_total = root.xpath("//cac:LegalMonetaryTotal", namespaces=ns)
        if not legal_monetary_total:
            raise ValueError("Invalid UBL: Missing LegalMonetaryTotal (mandatory)")
        total_node = legal_monetary_total[0]

        def get_total(path: str, field: str) -> Decimal:
            res = total_node.xpath(path, namespaces=ns)
            if res and getattr(res[0], "text", None):
                return BusinessReadySerializer._decimal_or_default(res[0].text, field, fallbacks)
            return BusinessReadySerializer._decimal_or_default(None, field, fallbacks)

        tax_total_res = root.xpath("//cac:TaxTotal/cbc:TaxAmount/text()", namespaces=ns)
        tax_total = BusinessReadySerializer._decimal_or_default(
            tax_total_res[0] if tax_total_res else None,
            "invoice.total_tax_amount",
            fallbacks,
        )

        fmt, profile = detect_format(root)
        output_format = fmt or "ubl"
        output_profile = profile or "xrechnung"
        if not fmt:
            BusinessReadySerializer._record_fallback(
                fallbacks,
                "invoice.format",
                "default_value",
                "missing",
                "ubl",
            )
        if not profile:
            BusinessReadySerializer._record_fallback(
                fallbacks,
                "invoice.profile",
                "default_value",
                "missing",
                "xrechnung",
            )

        raw_currency = xpath_first(root, "//cbc:DocumentCurrencyCode")
        currency = raw_currency or "EUR"
        if not raw_currency:
            BusinessReadySerializer._record_fallback(
                fallbacks,
                "invoice.currency",
                "default_value",
                "missing",
                "EUR",
            )

        return BusinessReadyInvoice(
            invoice_number=invoice_number,
            invoice_date=inv_date,
            currency=currency,
            buyer_reference=xpath_first(root, "//cbc:BuyerReference"),
            contract_reference=xpath_first(root, "//cac:ContractDocumentReference/cbc:ID"),
            seller=seller,
            buyer=buyer,
            line_items=line_items,
            tax_breakdown=BusinessReadySerializer._parse_ubl_tax_breakdown(root),
            total_net_amount=get_total("cbc:TaxExclusiveAmount", "invoice.total_net_amount"),
            total_tax_amount=tax_total,
            total_gross_amount=get_total("cbc:TaxInclusiveAmount", "invoice.total_gross_amount"),
            amount_due=get_total("cbc:PayableAmount", "invoice.amount_due"),
            format=output_format,
            profile=output_profile,
            due_date=due_date,
        )

    @staticmethod
    def _parse_ubl_party(
        node: etree._Element, fallbacks: List[Dict[str, Any]], party_prefix: str
    ) -> PartySchema:
        ns = BusinessReadySerializer.NS_UBL

        def get_text(xpath: str) -> str | None:
            res = node.xpath(xpath, namespaces=ns)
            return res[0] if res else None

        raw_name = get_text("cac:PartyName/cbc:Name/text()") or get_text(
            "cac:PartyLegalEntity/cbc:RegistrationName/text()"
        )
        name = raw_name or "Unknown"
        if not raw_name:
            BusinessReadySerializer._record_fallback(
                fallbacks,
                f"{party_prefix}.name",
                "placeholder_value",
                "missing",
                "Unknown",
            )

        line1 = get_text("cac:PostalAddress/cbc:StreetName/text()") or "..."
        if line1 == "...":
            BusinessReadySerializer._record_fallback(
                fallbacks,
                f"{party_prefix}.address.line1",
                "placeholder_value",
                "missing",
                "...",
            )

        city = get_text("cac:PostalAddress/cbc:CityName/text()") or "..."
        if city == "...":
            BusinessReadySerializer._record_fallback(
                fallbacks,
                f"{party_prefix}.address.city",
                "placeholder_value",
                "missing",
                "...",
            )

        postcode = get_text("cac:PostalAddress/cbc:PostalZone/text()") or "..."
        if postcode == "...":
            BusinessReadySerializer._record_fallback(
                fallbacks,
                f"{party_prefix}.address.postcode",
                "placeholder_value",
                "missing",
                "...",
            )

        raw_country = get_text("cac:PostalAddress/cac:Country/cbc:IdentificationCode/text()")
        country_code = raw_country or "FR"
        if not raw_country:
            BusinessReadySerializer._record_fallback(
                fallbacks,
                f"{party_prefix}.address.country_code",
                "default_value",
                "missing",
                "FR",
            )

        return PartySchema(
            name=name,
            vat_number=get_text("cac:PartyTaxScheme/cbc:CompanyID/text()"),
            registration_id=get_text("cac:PartyLegalEntity/cbc:CompanyID/text()"),
            email=get_text("cac:Contact/cbc:ElectronicMail/text()"),
            address=AddressSchema(
                line1=line1,
                city=city,
                postcode=postcode,
                country_code=country_code,
            ),
        )

    @staticmethod
    def _parse_ubl_line(
        node: etree._Element, fallbacks: List[Dict[str, Any]], line_index: int
    ) -> LineItemSchema:
        ns = BusinessReadySerializer.NS_UBL

        name = node.xpath("cac:Item/cbc:Name/text()", namespaces=ns)[0]
        qty = Decimal(node.xpath("cbc:InvoicedQuantity/text()", namespaces=ns)[0] or "1")
        price = Decimal(node.xpath("cac:Price/cbc:PriceAmount/text()", namespaces=ns)[0] or "0")
        total = Decimal(node.xpath("cbc:LineExtensionAmount/text()", namespaces=ns)[0] or "0")

        unit_code_candidates = node.xpath("cbc:InvoicedQuantity/@unitCode", namespaces=ns)
        unit_code = unit_code_candidates[0] if unit_code_candidates else "C62"
        if not unit_code_candidates:
            BusinessReadySerializer._record_fallback(
                fallbacks,
                f"invoice.line_items[{line_index}].unit_code",
                "default_value",
                "missing",
                "C62",
            )

        vat_raw = node.xpath("cac:Item/cac:ClassifiedTaxCategory/cbc:Percent/text()", namespaces=ns)[0]
        vat_rate = Decimal(vat_raw or "0")

        return LineItemSchema(
            name=name,
            quantity=qty,
            unit_code=unit_code,
            net_price=price,
            line_total=total,
            vat_rate=vat_rate,
        )

    @staticmethod
    def _parse_ubl_tax_breakdown(root: etree._Element) -> list:
        """Parse TaxSubtotal elements into TaxBreakdownSchema list."""
        ns = BusinessReadySerializer.NS_UBL

        def xpath_text(el: etree._Element, path: str) -> str | None:
            res = el.xpath(path + "/text()", namespaces=ns)
            return res[0] if res else None

        tax_nodes = root.xpath("//cac:TaxTotal/cac:TaxSubtotal", namespaces=ns)

        breakdown = []
        for node in tax_nodes:
            try:
                breakdown.append(
                    TaxBreakdownSchema(
                        category=xpath_text(node, "cac:TaxCategory/cbc:ID") or "S",
                        rate=Decimal(xpath_text(node, "cac:TaxCategory/cbc:Percent") or "0"),
                        basis_amount=Decimal(xpath_text(node, "cbc:TaxableAmount") or "0"),
                        tax_amount=Decimal(xpath_text(node, "cbc:TaxAmount") or "0"),
                    )
                )
            except Exception as e:
                logger.warning(f"Skipping malformed UBL tax entry: {e}")

        return breakdown
