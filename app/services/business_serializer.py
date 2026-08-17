"""Strict CII/UBL to normalized JSON mapping.

This module intentionally refuses malformed, incomplete, or unsupported input.
It never repairs XML, invents accounting values, or silently skips material data.
"""

from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal, InvalidOperation
from typing import Any

from lxml import etree

from app.schemas.integration import (
    AddressSchema,
    BusinessReadyInvoice,
    LineItemSchema,
    PartySchema,
    SerializationDiagnostic,
    TaxBreakdownSchema,
)


class SerializationMappingError(ValueError):
    """The source cannot be represented by the strict normalized contract."""

    def __init__(self, diagnostics: list[SerializationDiagnostic]):
        self.diagnostics = diagnostics
        super().__init__(diagnostics[0].message if diagnostics else "Serialization failed")


class BusinessReadySerializer:
    """Map supported CII and UBL invoices without recovery or defaults."""

    NS_CII = {
        "rsm": "urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100",
        "ram": "urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100",
        "udt": "urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100",
    }
    NS_UBL = {
        "ubl": "urn:oasis:names:specification:ubl:schema:xsd:Invoice-2",
        "cac": "urn:oasis:names:specification:ubl:schema:xsd:CommonAggregateComponents-2",
        "cbc": "urn:oasis:names:specification:ubl:schema:xsd:CommonBasicComponents-2",
    }

    @classmethod
    def serialize(cls, xml_bytes: bytes, is_pro: bool = False) -> BusinessReadyInvoice:
        """Return a complete normalized invoice or raise ``SerializationMappingError``.

        ``is_pro`` is accepted for API compatibility only. It never changes mapping
        semantics: strictness is a data-safety property, not a licensing tier.
        """

        del is_pro
        root = cls._parse_xml(xml_bytes)
        qname = etree.QName(root)

        if qname.localname == "CrossIndustryInvoice" and qname.namespace == cls.NS_CII["rsm"]:
            cls._reject_unsupported_cii(root)
            invoice = cls._parse_cii(root)
        elif qname.localname == "Invoice" and qname.namespace == cls.NS_UBL["ubl"]:
            cls._reject_unsupported_ubl(root)
            invoice = cls._parse_ubl(root)
        else:
            cls._fail(
                "UNSUPPORTED_DOCUMENT",
                "Only CII CrossIndustryInvoice and UBL Invoice documents are supported.",
                "/",
                source="xml",
            )

        cls._check_invariants(invoice)
        return invoice

    @classmethod
    def serialize_with_diagnostics(
        cls, xml_bytes: bytes, is_pro: bool = False
    ) -> tuple[BusinessReadyInvoice, list[dict[str, Any]], bool]:
        """Compatibility wrapper for callers of the former fallback API.

        A successful strict mapping can never contain fallbacks or XML recovery.
        """

        return cls.serialize(xml_bytes, is_pro=is_pro), [], False

    @classmethod
    def _parse_xml(cls, xml_bytes: bytes) -> etree._Element:
        parser = etree.XMLParser(
            recover=False,
            resolve_entities=False,
            no_network=True,
            huge_tree=False,
            load_dtd=False,
        )
        try:
            return etree.fromstring(xml_bytes, parser=parser)
        except etree.XMLSyntaxError as exc:
            line, column = exc.position
            cls._fail(
                "XML_MALFORMED",
                f"The XML is not well formed: {exc.msg}",
                f"line:{line}:column:{column}",
                source="xml",
            )

    @staticmethod
    def _diagnostic(
        code: str,
        message: str,
        path: str | None,
        source: str = "mapping",
    ) -> SerializationDiagnostic:
        return SerializationDiagnostic(
            code=code,
            message=message,
            path=path,
            source=source,
        )

    @classmethod
    def _fail(
        cls,
        code: str,
        message: str,
        path: str | None,
        source: str = "mapping",
    ) -> None:
        raise SerializationMappingError([cls._diagnostic(code, message, path, source)])

    @classmethod
    def _text(
        cls,
        node: etree._Element,
        path: str,
        namespaces: dict[str, str],
    ) -> str | None:
        result = node.xpath(path, namespaces=namespaces)
        if not result:
            return None
        value = result[0]
        if isinstance(value, etree._Element):
            value = value.text
        if value is None:
            return None
        text = str(value).strip()
        return text or None

    @classmethod
    def _required_text(
        cls,
        node: etree._Element,
        path: str,
        namespaces: dict[str, str],
        field: str,
    ) -> str:
        value = cls._text(node, path, namespaces)
        if value is None:
            cls._fail(
                "MAPPING_REQUIRED_VALUE_MISSING",
                f"Required value '{field}' is missing.",
                path,
            )
        return value

    @classmethod
    def _required_decimal(
        cls,
        node: etree._Element,
        path: str,
        namespaces: dict[str, str],
        field: str,
    ) -> Decimal:
        raw = cls._required_text(node, path, namespaces, field)
        try:
            return Decimal(raw)
        except InvalidOperation:
            cls._fail(
                "MAPPING_INVALID_DECIMAL",
                f"Value '{raw}' for '{field}' is not a valid decimal.",
                path,
            )

    @classmethod
    def _required_date(
        cls,
        node: etree._Element,
        path: str,
        namespaces: dict[str, str],
        field: str,
    ) -> date:
        raw = cls._required_text(node, path, namespaces, field)
        for date_format in ("%Y%m%d", "%Y-%m-%d"):
            try:
                return datetime.strptime(raw, date_format).date()
            except ValueError:
                continue
        cls._fail(
            "MAPPING_INVALID_DATE",
            f"Value '{raw}' for '{field}' is not a supported calendar date.",
            path,
        )

    @classmethod
    def _optional_date(
        cls,
        node: etree._Element,
        path: str,
        namespaces: dict[str, str],
        field: str,
    ) -> date | None:
        raw = cls._text(node, path, namespaces)
        if raw is None:
            return None
        for date_format in ("%Y%m%d", "%Y-%m-%d"):
            try:
                return datetime.strptime(raw, date_format).date()
            except ValueError:
                continue
        cls._fail(
            "MAPPING_INVALID_DATE",
            f"Value '{raw}' for '{field}' is not a supported calendar date.",
            path,
        )

    @classmethod
    def _reject_unsupported_cii(cls, root: etree._Element) -> None:
        unsupported = [
            ("//ram:SpecifiedTradeAllowanceCharge", "allowances or charges"),
            ("//ram:BillingSpecifiedPeriod", "billing periods"),
            ("//ram:AttachmentBinaryObject", "embedded attachments"),
        ]
        cls._reject_elements(root, unsupported, cls.NS_CII)

    @classmethod
    def _reject_unsupported_ubl(cls, root: etree._Element) -> None:
        unsupported = [
            ("//cac:AllowanceCharge", "allowances or charges"),
            ("//cac:InvoicePeriod", "billing periods"),
            ("//cac:Attachment", "embedded attachments"),
        ]
        cls._reject_elements(root, unsupported, cls.NS_UBL)

    @classmethod
    def _reject_elements(
        cls,
        root: etree._Element,
        unsupported: list[tuple[str, str]],
        namespaces: dict[str, str],
    ) -> None:
        diagnostics = []
        for path, label in unsupported:
            if root.xpath(path, namespaces=namespaces):
                diagnostics.append(
                    cls._diagnostic(
                        "MAPPING_UNSUPPORTED_ELEMENT",
                        f"The current schema does not map {label}; the invoice was not partially serialized.",
                        path,
                    )
                )
        if diagnostics:
            raise SerializationMappingError(diagnostics)

    @classmethod
    def _parse_cii(cls, root: etree._Element) -> BusinessReadyInvoice:
        ns = cls.NS_CII
        seller_nodes = root.xpath("//ram:SellerTradeParty", namespaces=ns)
        buyer_nodes = root.xpath("//ram:BuyerTradeParty", namespaces=ns)
        line_nodes = root.xpath("//ram:IncludedSupplyChainTradeLineItem", namespaces=ns)
        totals_nodes = root.xpath(
            "//ram:SpecifiedTradeSettlementHeaderMonetarySummation", namespaces=ns
        )
        if not seller_nodes:
            cls._fail("MAPPING_REQUIRED_GROUP_MISSING", "SellerTradeParty is missing.", "//ram:SellerTradeParty")
        if not buyer_nodes:
            cls._fail("MAPPING_REQUIRED_GROUP_MISSING", "BuyerTradeParty is missing.", "//ram:BuyerTradeParty")
        if not line_nodes:
            cls._fail(
                "MAPPING_UNSUPPORTED_PROFILE",
                "The invoice contains no line items and cannot produce the strict line-level contract.",
                "//ram:IncludedSupplyChainTradeLineItem",
            )
        if not totals_nodes:
            cls._fail(
                "MAPPING_REQUIRED_GROUP_MISSING",
                "Header monetary totals are missing.",
                "//ram:SpecifiedTradeSettlementHeaderMonetarySummation",
            )

        totals = totals_nodes[0]
        return BusinessReadyInvoice(
            invoice_number=cls._required_text(
                root, "//rsm:ExchangedDocument/ram:ID/text()", ns, "invoice_number"
            ),
            document_type_code=cls._required_text(
                root, "//rsm:ExchangedDocument/ram:TypeCode/text()", ns, "document_type_code"
            ),
            invoice_date=cls._required_date(
                root,
                "//rsm:ExchangedDocument/ram:IssueDateTime/udt:DateTimeString/text()",
                ns,
                "invoice_date",
            ),
            due_date=cls._optional_date(
                root,
                "//ram:SpecifiedTradePaymentTerms/ram:DueDateDateTime/udt:DateTimeString/text()",
                ns,
                "due_date",
            ),
            currency=cls._required_text(
                root, "//ram:InvoiceCurrencyCode/text()", ns, "currency"
            ),
            buyer_reference=cls._text(
                root, "//ram:ApplicableHeaderTradeAgreement/ram:BuyerReference/text()", ns
            ),
            purchase_order_reference=cls._text(
                root,
                "//ram:BuyerOrderReferencedDocument/ram:IssuerAssignedID/text()",
                ns,
            ),
            contract_reference=cls._text(
                root,
                "//ram:ContractReferencedDocument/ram:IssuerAssignedID/text()",
                ns,
            ),
            preceding_invoice_reference=cls._text(
                root,
                "//ram:InvoiceReferencedDocument/ram:IssuerAssignedID/text()",
                ns,
            ),
            payment_means_code=cls._text(
                root, "//ram:SpecifiedTradeSettlementPaymentMeans/ram:TypeCode/text()", ns
            ),
            payment_reference=cls._text(
                root, "//ram:PaymentReference/text()", ns
            ),
            iban=cls._text(
                root,
                "//ram:PayeePartyCreditorFinancialAccount/ram:IBANID/text()",
                ns,
            ),
            seller=cls._parse_cii_party(seller_nodes[0], "seller"),
            buyer=cls._parse_cii_party(buyer_nodes[0], "buyer"),
            line_items=[cls._parse_cii_line(node, index) for index, node in enumerate(line_nodes)],
            tax_breakdown=cls._parse_cii_tax_breakdown(root),
            total_net_amount=cls._required_decimal(
                totals, "ram:TaxBasisTotalAmount/text()", ns, "total_net_amount"
            ),
            total_tax_amount=cls._required_decimal(
                totals, "ram:TaxTotalAmount/text()", ns, "total_tax_amount"
            ),
            total_gross_amount=cls._required_decimal(
                totals, "ram:GrandTotalAmount/text()", ns, "total_gross_amount"
            ),
            amount_due=cls._required_decimal(
                totals, "ram:DuePayableAmount/text()", ns, "amount_due"
            ),
            format="cii",
            profile=cls._cii_profile(root),
        )

    @classmethod
    def _parse_cii_party(cls, node: etree._Element, label: str) -> PartySchema:
        ns = cls.NS_CII
        address_values = {
            "line1": cls._text(node, "ram:PostalTradeAddress/ram:LineOne/text()", ns),
            "line2": cls._text(node, "ram:PostalTradeAddress/ram:LineTwo/text()", ns),
            "city": cls._text(node, "ram:PostalTradeAddress/ram:CityName/text()", ns),
            "postcode": cls._text(node, "ram:PostalTradeAddress/ram:PostcodeCode/text()", ns),
            "country_code": cls._text(node, "ram:PostalTradeAddress/ram:CountryID/text()", ns),
        }
        electronic_address = cls._text(
            node, "ram:URIUniversalCommunication/ram:URIID/text()", ns
        )
        electronic_scheme = cls._text(
            node, "ram:URIUniversalCommunication/ram:URIID/@schemeID", ns
        )
        vat_number = cls._text(
            node, "ram:SpecifiedTaxRegistration/ram:ID[@schemeID='VA']/text()", ns
        ) or cls._text(node, "ram:SpecifiedTaxRegistration/ram:ID/text()", ns)

        return PartySchema(
            name=cls._required_text(node, "ram:Name/text()", ns, f"{label}.name"),
            vat_number=vat_number,
            registration_id=cls._text(
                node, "ram:SpecifiedLegalOrganization/ram:ID/text()", ns
            ),
            electronic_address=electronic_address,
            electronic_address_scheme=electronic_scheme,
            email=cls._text(
                node,
                "ram:DefinedTradeContact/ram:EmailURIUniversalCommunication/ram:URIID/text()",
                ns,
            ),
            address=AddressSchema(**address_values) if any(address_values.values()) else None,
        )

    @classmethod
    def _parse_cii_line(cls, node: etree._Element, index: int) -> LineItemSchema:
        ns = cls.NS_CII
        prefix = f"line_items[{index}]"
        return LineItemSchema(
            line_id=cls._text(node, "ram:AssociatedDocumentLineDocument/ram:LineID/text()", ns),
            name=cls._required_text(
                node, ".//ram:SpecifiedTradeProduct/ram:Name/text()", ns, f"{prefix}.name"
            ),
            description=cls._text(
                node, ".//ram:SpecifiedTradeProduct/ram:Description/text()", ns
            ),
            quantity=cls._required_decimal(
                node, ".//ram:BilledQuantity/text()", ns, f"{prefix}.quantity"
            ),
            unit_code=cls._required_text(
                node, ".//ram:BilledQuantity/@unitCode", ns, f"{prefix}.unit_code"
            ),
            net_price=cls._required_decimal(
                node,
                ".//ram:NetPriceProductTradePrice/ram:ChargeAmount/text()",
                ns,
                f"{prefix}.net_price",
            ),
            line_total=cls._required_decimal(
                node,
                ".//ram:SpecifiedTradeSettlementLineMonetarySummation/ram:LineTotalAmount/text()",
                ns,
                f"{prefix}.line_total",
            ),
            vat_rate=cls._required_decimal(
                node,
                ".//ram:ApplicableTradeTax/ram:RateApplicablePercent/text()",
                ns,
                f"{prefix}.vat_rate",
            ),
            vat_category=cls._required_text(
                node,
                ".//ram:ApplicableTradeTax/ram:CategoryCode/text()",
                ns,
                f"{prefix}.vat_category",
            ),
            seller_assigned_id=cls._text(
                node, ".//ram:SpecifiedTradeProduct/ram:SellerAssignedID/text()", ns
            ),
            buyer_assigned_id=cls._text(
                node, ".//ram:SpecifiedTradeProduct/ram:BuyerAssignedID/text()", ns
            ),
        )

    @classmethod
    def _parse_cii_tax_breakdown(cls, root: etree._Element) -> list[TaxBreakdownSchema]:
        ns = cls.NS_CII
        nodes = root.xpath(
            "//ram:ApplicableHeaderTradeSettlement/ram:ApplicableTradeTax", namespaces=ns
        )
        if not nodes:
            cls._fail(
                "MAPPING_REQUIRED_GROUP_MISSING",
                "Header tax breakdown is missing.",
                "//ram:ApplicableHeaderTradeSettlement/ram:ApplicableTradeTax",
            )
        return [
            TaxBreakdownSchema(
                category=cls._required_text(node, "ram:CategoryCode/text()", ns, f"tax_breakdown[{index}].category"),
                rate=cls._required_decimal(node, "ram:RateApplicablePercent/text()", ns, f"tax_breakdown[{index}].rate"),
                basis_amount=cls._required_decimal(node, "ram:BasisAmount/text()", ns, f"tax_breakdown[{index}].basis_amount"),
                tax_amount=cls._required_decimal(node, "ram:CalculatedAmount/text()", ns, f"tax_breakdown[{index}].tax_amount"),
            )
            for index, node in enumerate(nodes)
        ]

    @classmethod
    def _parse_ubl(cls, root: etree._Element) -> BusinessReadyInvoice:
        ns = cls.NS_UBL
        seller_nodes = root.xpath("//cac:AccountingSupplierParty/cac:Party", namespaces=ns)
        buyer_nodes = root.xpath("//cac:AccountingCustomerParty/cac:Party", namespaces=ns)
        line_nodes = root.xpath("//cac:InvoiceLine", namespaces=ns)
        totals_nodes = root.xpath("//cac:LegalMonetaryTotal", namespaces=ns)
        if not seller_nodes:
            cls._fail("MAPPING_REQUIRED_GROUP_MISSING", "AccountingSupplierParty is missing.", "//cac:AccountingSupplierParty")
        if not buyer_nodes:
            cls._fail("MAPPING_REQUIRED_GROUP_MISSING", "AccountingCustomerParty is missing.", "//cac:AccountingCustomerParty")
        if not line_nodes:
            cls._fail("MAPPING_REQUIRED_GROUP_MISSING", "InvoiceLine is missing.", "//cac:InvoiceLine")
        if not totals_nodes:
            cls._fail("MAPPING_REQUIRED_GROUP_MISSING", "LegalMonetaryTotal is missing.", "//cac:LegalMonetaryTotal")

        totals = totals_nodes[0]
        tax_total_nodes = root.xpath("//cac:TaxTotal[1]", namespaces=ns)
        if not tax_total_nodes:
            cls._fail("MAPPING_REQUIRED_GROUP_MISSING", "TaxTotal is missing.", "//cac:TaxTotal")

        return BusinessReadyInvoice(
            invoice_number=cls._required_text(root, "/ubl:Invoice/cbc:ID/text()", ns, "invoice_number"),
            document_type_code=cls._required_text(root, "/ubl:Invoice/cbc:InvoiceTypeCode/text()", ns, "document_type_code"),
            invoice_date=cls._required_date(root, "/ubl:Invoice/cbc:IssueDate/text()", ns, "invoice_date"),
            due_date=cls._optional_date(root, "/ubl:Invoice/cbc:DueDate/text()", ns, "due_date"),
            currency=cls._required_text(root, "/ubl:Invoice/cbc:DocumentCurrencyCode/text()", ns, "currency"),
            buyer_reference=cls._text(root, "/ubl:Invoice/cbc:BuyerReference/text()", ns),
            purchase_order_reference=cls._text(root, "//cac:OrderReference/cbc:ID/text()", ns),
            contract_reference=cls._text(root, "//cac:ContractDocumentReference/cbc:ID/text()", ns),
            preceding_invoice_reference=cls._text(root, "//cac:BillingReference/cac:InvoiceDocumentReference/cbc:ID/text()", ns),
            payment_means_code=cls._text(root, "//cac:PaymentMeans/cbc:PaymentMeansCode/text()", ns),
            payment_reference=cls._text(root, "//cac:PaymentMeans/cbc:PaymentID/text()", ns),
            iban=cls._text(root, "//cac:PaymentMeans/cac:PayeeFinancialAccount/cbc:ID/text()", ns),
            seller=cls._parse_ubl_party(seller_nodes[0], "seller"),
            buyer=cls._parse_ubl_party(buyer_nodes[0], "buyer"),
            line_items=[cls._parse_ubl_line(node, index) for index, node in enumerate(line_nodes)],
            tax_breakdown=cls._parse_ubl_tax_breakdown(root),
            total_net_amount=cls._required_decimal(totals, "cbc:TaxExclusiveAmount/text()", ns, "total_net_amount"),
            total_tax_amount=cls._required_decimal(tax_total_nodes[0], "cbc:TaxAmount/text()", ns, "total_tax_amount"),
            total_gross_amount=cls._required_decimal(totals, "cbc:TaxInclusiveAmount/text()", ns, "total_gross_amount"),
            amount_due=cls._required_decimal(totals, "cbc:PayableAmount/text()", ns, "amount_due"),
            format="ubl",
            profile=cls._ubl_profile(root),
        )

    @classmethod
    def _parse_ubl_party(cls, node: etree._Element, label: str) -> PartySchema:
        ns = cls.NS_UBL
        address_values = {
            "line1": cls._text(node, "cac:PostalAddress/cbc:StreetName/text()", ns),
            "line2": cls._text(node, "cac:PostalAddress/cbc:AdditionalStreetName/text()", ns),
            "city": cls._text(node, "cac:PostalAddress/cbc:CityName/text()", ns),
            "postcode": cls._text(node, "cac:PostalAddress/cbc:PostalZone/text()", ns),
            "country_code": cls._text(node, "cac:PostalAddress/cac:Country/cbc:IdentificationCode/text()", ns),
        }
        name = cls._text(node, "cac:PartyName/cbc:Name/text()", ns) or cls._text(
            node, "cac:PartyLegalEntity/cbc:RegistrationName/text()", ns
        )
        if name is None:
            cls._fail(
                "MAPPING_REQUIRED_VALUE_MISSING",
                f"Required value '{label}.name' is missing.",
                "cac:PartyName/cbc:Name | cac:PartyLegalEntity/cbc:RegistrationName",
            )
        electronic_address = cls._text(node, "cbc:EndpointID/text()", ns)
        return PartySchema(
            name=name,
            vat_number=cls._text(node, "cac:PartyTaxScheme/cbc:CompanyID/text()", ns),
            registration_id=cls._text(node, "cac:PartyLegalEntity/cbc:CompanyID/text()", ns),
            electronic_address=electronic_address,
            electronic_address_scheme=cls._text(node, "cbc:EndpointID/@schemeID", ns),
            email=cls._text(node, "cac:Contact/cbc:ElectronicMail/text()", ns),
            address=AddressSchema(**address_values) if any(address_values.values()) else None,
        )

    @classmethod
    def _parse_ubl_line(cls, node: etree._Element, index: int) -> LineItemSchema:
        ns = cls.NS_UBL
        prefix = f"line_items[{index}]"
        return LineItemSchema(
            line_id=cls._text(node, "cbc:ID/text()", ns),
            name=cls._required_text(node, "cac:Item/cbc:Name/text()", ns, f"{prefix}.name"),
            description=cls._text(node, "cac:Item/cbc:Description/text()", ns),
            quantity=cls._required_decimal(node, "cbc:InvoicedQuantity/text()", ns, f"{prefix}.quantity"),
            unit_code=cls._required_text(node, "cbc:InvoicedQuantity/@unitCode", ns, f"{prefix}.unit_code"),
            net_price=cls._required_decimal(node, "cac:Price/cbc:PriceAmount/text()", ns, f"{prefix}.net_price"),
            line_total=cls._required_decimal(node, "cbc:LineExtensionAmount/text()", ns, f"{prefix}.line_total"),
            vat_rate=cls._required_decimal(node, "cac:Item/cac:ClassifiedTaxCategory/cbc:Percent/text()", ns, f"{prefix}.vat_rate"),
            vat_category=cls._required_text(node, "cac:Item/cac:ClassifiedTaxCategory/cbc:ID/text()", ns, f"{prefix}.vat_category"),
            seller_assigned_id=cls._text(node, "cac:Item/cac:SellersItemIdentification/cbc:ID/text()", ns),
            buyer_assigned_id=cls._text(node, "cac:Item/cac:BuyersItemIdentification/cbc:ID/text()", ns),
        )

    @classmethod
    def _parse_ubl_tax_breakdown(cls, root: etree._Element) -> list[TaxBreakdownSchema]:
        ns = cls.NS_UBL
        nodes = root.xpath("//cac:TaxTotal/cac:TaxSubtotal", namespaces=ns)
        if not nodes:
            cls._fail(
                "MAPPING_REQUIRED_GROUP_MISSING",
                "TaxSubtotal is missing.",
                "//cac:TaxTotal/cac:TaxSubtotal",
            )
        return [
            TaxBreakdownSchema(
                category=cls._required_text(node, "cac:TaxCategory/cbc:ID/text()", ns, f"tax_breakdown[{index}].category"),
                rate=cls._required_decimal(node, "cac:TaxCategory/cbc:Percent/text()", ns, f"tax_breakdown[{index}].rate"),
                basis_amount=cls._required_decimal(node, "cbc:TaxableAmount/text()", ns, f"tax_breakdown[{index}].basis_amount"),
                tax_amount=cls._required_decimal(node, "cbc:TaxAmount/text()", ns, f"tax_breakdown[{index}].tax_amount"),
            )
            for index, node in enumerate(nodes)
        ]

    @classmethod
    def _cii_profile(cls, root: etree._Element) -> str | None:
        raw = cls._text(
            root,
            "//ram:GuidelineSpecifiedDocumentContextParameter/ram:ID/text()",
            cls.NS_CII,
        )
        return cls._profile_label(raw)

    @classmethod
    def _ubl_profile(cls, root: etree._Element) -> str | None:
        raw = cls._text(root, "/ubl:Invoice/cbc:CustomizationID/text()", cls.NS_UBL)
        return cls._profile_label(raw)

    @staticmethod
    def _profile_label(raw: str | None) -> str | None:
        if raw is None:
            return None
        normalized = raw.lower()
        if "xrechnung_3.0" in normalized:
            return "xrechnung_3.0"
        for marker, label in (
            ("xrechnung", "xrechnung"),
            ("extended", "extended"),
            ("en16931", "en16931"),
            ("basicwl", "basicwl"),
            ("basic", "basic"),
            ("minimum", "minimum"),
        ):
            if marker in normalized:
                return label
        return raw

    @classmethod
    def _check_invariants(cls, invoice: BusinessReadyInvoice) -> None:
        expected_gross = invoice.total_net_amount + invoice.total_tax_amount
        if abs(expected_gross - invoice.total_gross_amount) > Decimal("0.01"):
            cls._fail(
                "INVARIANT_TOTALS_MISMATCH",
                "total_gross_amount does not equal total_net_amount plus total_tax_amount.",
                "invoice.total_gross_amount",
                source="invariant",
            )
