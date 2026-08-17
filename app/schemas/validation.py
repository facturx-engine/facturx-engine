"""
Pydantic models for API request/response validation.
"""
from decimal import Decimal, InvalidOperation
from typing import Any, Dict, List, Literal, Optional, Union

from pydantic import BaseModel, Field, model_validator


class Address(BaseModel):
    """Physical address."""
    line1: str = Field(..., description="Main address line")
    line2: Optional[str] = Field(None, description="Additional address line")
    postcode: str = Field(..., description="Postal code")
    city: str = Field(..., description="City name")
    country_code: str = Field(..., description="ISO 3166-1 alpha-2 country code")


class BillingPeriod(BaseModel):
    """Period for billing or delivery."""
    start: str = Field(..., description="Start date (YYYYMMDD)")
    end: str = Field(..., description="End date (YYYYMMDD)")


class ShipToParty(BaseModel):
    """Ship-to / Delivery party information."""
    id: Optional[str] = Field(None, description="Internal delivery location ID")
    global_id: Optional[str] = Field(None, description="Global location ID (e.g. GLN)")
    global_id_scheme: Optional[str] = Field(None, description="Global ID scheme (default: 0088 for GLN)")
    name: str = Field(..., description="Name of the recipient")
    address: Address


class AllowanceCharge(BaseModel):
    """Allowance or Charge detail."""
    amount: float = Field(..., description="Amount")
    reason: Optional[str] = Field(None, description="Reason text")
    reason_code: Optional[str] = Field(None, description="Reason code (UN/TDID 5189 for allowances, 7161 for charges)")
    vat_category: str = Field(..., description="VAT category code")
    vat_rate: float = Field(..., description="VAT rate percent")


class PaymentDiscount(BaseModel):
    """Payment discount terms."""
    days: int = Field(..., description="Number of days")
    percent: float = Field(..., description="Discount percentage")


class SellerInfo(BaseModel):
    """Seller (Supplier) information."""
    name: str = Field(..., description="Seller company name")
    address: Optional[Address] = Field(None, description="Physical address (Mandatory for EN16931)")
    tax_number: Optional[str] = Field(None, description="Tax number (FC scheme)")
    vat_number: Optional[str] = Field(None, description="VAT identification number (VA scheme)")
    siren: Optional[str] = Field(None, description="SIREN legal identifier (France, 9 digits)")
    siret: Optional[str] = Field(None, description="SIRET (France specific)")
    electronic_address: Optional[str] = Field(None, description="Electronic routing address (BT-34)")
    electronic_address_scheme: Optional[str] = Field(None, description="Electronic address scheme ID (default: 0225 for French SIREN)")
    global_id: Optional[str] = Field(None, description="Global Identifier (e.g. DUNS, GLN)")
    global_id_scheme: Optional[str] = Field(None, description="Scheme ID for Global ID (default: 0088 for GLN)")
    contact_name: Optional[str] = Field(None, description="Contact person name")
    phone: Optional[str] = Field(None, description="Phone number")
    email: Optional[str] = Field(None, description="Email address")
    iban: Optional[str] = Field(None, description="IBAN (Seller only)")
    bic: Optional[str] = Field(None, description="BIC (Seller only)")
    bank_name: Optional[str] = Field(None, description="Bank Name (Seller only)")
    id: Optional[str] = Field(None, description="Buyer-assigned seller ID")


class BuyerInfo(BaseModel):
    """Buyer (Customer) information."""
    name: str = Field(..., description="Buyer company name")
    address: Optional[Address] = Field(None, description="Physical address")
    vat_number: Optional[str] = Field(None, description="VAT identification number")
    siren: Optional[str] = Field(None, description="SIREN legal identifier (France, 9 digits)")
    siret: Optional[str] = Field(None, description="SIRET (France specific)")
    electronic_address: Optional[str] = Field(None, description="Electronic routing address (BT-49)")
    electronic_address_scheme: Optional[str] = Field(None, description="Electronic address scheme ID (default: 0225 for French SIREN)")
    global_id: Optional[str] = Field(None, description="Global Identifier")
    global_id_scheme: Optional[str] = Field(None, description="Scheme ID for Global ID")
    contact_name: Optional[str] = Field(None, description="Contact person name")
    phone: Optional[str] = Field(None, description="Phone number")
    email: Optional[str] = Field(None, description="Email address")
    id: Optional[str] = Field(None, description="Seller-assigned buyer ID (Customer Number)")


class TaxDetail(BaseModel):
    """Tax breakdown per category/rate."""
    calculated_amount: str = Field(..., description="Tax amount")
    basis_amount: str = Field(..., description="Taxable basis amount")
    rate: str = Field(..., description="VAT rate (e.g. 20.00)")
    category_code: str = Field(default="S", description="VAT Category Code (S=Standard, Z=Zero...)")


class LineItem(BaseModel):
    """Invoice line item."""
    line_id: str = Field(default="1", description="Line number")
    name: str = Field(..., description="Product/Service name")
    quantity: float = Field(..., description="Billed quantity")
    unit_code: str = Field(default="C62", description="Unit code (C62=Unit)")
    net_price: float = Field(..., description="Net unit price")
    net_total: float = Field(..., description="Net line total (Qty * Price)")
    vat_rate: float = Field(..., description="VAT rate percent")
    vat_category: str = Field(default="S", description="VAT category code")
    note: Optional[str] = Field(None, description="Line note")
    global_id: Optional[str] = Field(None, description="Product Global ID (e.g. GTIN)")
    global_id_scheme: Optional[str] = Field(None, description="Scheme ID for Global ID (default: 0160 for GTIN)")
    seller_assigned_id: Optional[str] = Field(None, description="Seller's article number")
    buyer_assigned_id: Optional[str] = Field(None, description="Buyer's article number")
    description: Optional[str] = Field(None, description="Detailed description")
    country_of_origin: Optional[str] = Field(None, description="ISO country code of origin")
    gross_price: Optional[float] = Field(None, description="Gross price before line discount")
    price_discount: Optional[float] = Field(None, description="Line level discount amount")
    billing_period: Optional[BillingPeriod] = Field(None, description="Line specific billing period")


class MonetaryAmounts(BaseModel):
    """Monetary summary amounts."""
    tax_basis_total: str = Field(..., description="Total amount excluding VAT")
    tax_total: str = Field(..., description="Total VAT amount")
    grand_total: str = Field(..., description="Total amount including VAT")
    due_payable: str = Field(..., description="Amount due for payment")
    line_total: Optional[str] = Field(None, description="Sum of line net amounts")
    charge_total: Optional[str] = Field(None, description="Total charges")
    allowance_total: Optional[str] = Field(None, description="Total allowances")
    prepaid: Optional[str] = Field(None, description="Amount already paid")


class InvoiceMetadata(BaseModel):
    """Invoice metadata for Factur-X generation."""
    invoice_number: str = Field(..., description="Unique invoice identifier")
    issue_date: str = Field(..., description="Invoice issue date (YYYYMMDD format)")
    seller: SellerInfo
    buyer: BuyerInfo
    lines: List[LineItem] = Field(default_factory=list, description="Line items")
    tax_details: List[TaxDetail] = Field(default_factory=list, description="Tax breakdown details")
    amounts: MonetaryAmounts
    currency_code: str = Field(default="EUR", description="ISO 4217 currency code")
    profile: Literal["minimum", "basicwl", "basic", "en16931", "extended", "xrechnung_3.0"] = Field(
        default="en16931",
        description="Factur-X profile level"
    )
    due_date: Optional[str] = Field(None, description="Payment due date (YYYYMMDD format)")
    payment_terms: Optional[str] = Field(None, description="Payment terms description")
    document_type_code: str = Field(default="380", description="Document type code (380=Commercial Invoice)")
    business_process_type: Optional[str] = Field(None, description="Business process type / billing mode (BT-23, e.g. B1 for France)")
    notes: Optional[List[Union[str, dict]]] = Field(None, description="Header notes")
    buyer_reference: Optional[str] = Field(None, description="Buyer reference (e.g. order number)")
    contract_reference: Optional[str] = Field(None, description="Contract reference")
    delivery_date: Optional[str] = Field(None, description="Actual delivery date (YYYYMMDD)")
    ship_to: Optional[ShipToParty] = Field(None, description="Delivery party/address")
    creditor_reference: Optional[str] = Field(None, description="Creditor Reference ID (e.g. SEPA)")
    allowances: Optional[List[AllowanceCharge]] = Field(None, description="Document level allowances")
    charges: Optional[List[AllowanceCharge]] = Field(None, description="Document level charges")
    payment_discount: Optional[PaymentDiscount] = Field(None, description="Payment discount terms")
    payment_means_code: Optional[str] = Field(None, description="Payment means code (e.g. 58=SEPA, 10=Cash)")

    @model_validator(mode="after")
    def validate_generation_contract(self) -> "InvoiceMetadata":
        """Reject incomplete or arithmetically inconsistent generation input.

        The generator must not manufacture a tax breakdown or postal address to
        make an otherwise incomplete invoice look usable.
        """

        line_level_profiles = {"basic", "en16931", "extended", "xrechnung_3.0"}
        if self.profile in line_level_profiles:
            if not self.lines:
                raise ValueError(f"profile '{self.profile}' requires at least one line")
            if not self.tax_details:
                raise ValueError(
                    f"profile '{self.profile}' requires an explicit tax_details breakdown"
                )
            if self.seller.address is None or self.buyer.address is None:
                raise ValueError(
                    f"profile '{self.profile}' requires explicit seller and buyer postal addresses"
                )

        try:
            basis_total = Decimal(self.amounts.tax_basis_total)
            tax_total = Decimal(self.amounts.tax_total)
            gross_total = Decimal(self.amounts.grand_total)
            due_total = Decimal(self.amounts.due_payable)
            prepaid = Decimal(self.amounts.prepaid or "0")
            breakdown_basis = sum(
                (Decimal(item.basis_amount) for item in self.tax_details), Decimal("0")
            )
            breakdown_tax = sum(
                (Decimal(item.calculated_amount) for item in self.tax_details),
                Decimal("0"),
            )
        except InvalidOperation as exc:
            raise ValueError("monetary amounts and tax_details must contain valid decimals") from exc

        tolerance = Decimal("0.01")
        if self.tax_details and abs(breakdown_basis - basis_total) > tolerance:
            raise ValueError("tax_details basis sum does not match amounts.tax_basis_total")
        if self.tax_details and abs(breakdown_tax - tax_total) > tolerance:
            raise ValueError("tax_details tax sum does not match amounts.tax_total")
        if abs((basis_total + tax_total) - gross_total) > tolerance:
            raise ValueError("amounts.grand_total must equal tax_basis_total plus tax_total")
        if abs((gross_total - prepaid) - due_total) > tolerance:
            raise ValueError("amounts.due_payable must equal grand_total minus prepaid")

        return self


class ValidationErrorDetail(BaseModel):
    """Structured technical validation error."""
    rule_id: Optional[str] = Field(None, description="Rule identifier (e.g. BR-CO-10)")
    message: str = Field(..., description="Error message")
    severity: str = Field(default="error", description="error or warning")


class SkippedLayer(BaseModel):
    """A validation layer that was skipped, with the reason why."""
    layer: str = Field(..., description="Layer name (xsd, schematron, pdfa3b, br_fr_ctc)")
    reason: str = Field(..., description="Why this layer was skipped (e.g. tool_missing:saxon_jar)")


class ProHint(BaseModel):
    """Legacy compatibility shape for an enhanced-diagnostics summary."""
    error_count: int = Field(..., description="Number of errors in the summary")
    warning_count: int = Field(..., description="Number of warnings in the summary")
    message: str = Field(..., description="Human-readable diagnostics note")


class ValidationResult(BaseModel):
    """Validation result response."""
    valid: bool = Field(..., description="Whether the file is valid")
    format: Optional[str] = Field(None, description="Detected format (factur-x, zugferd, ubl)")
    flavor: Optional[str] = Field(None, description="Detected flavor/level")
    errors: List[ValidationErrorDetail] = Field(default_factory=list, description="List of validation errors")
    validation_mode: Optional[str] = Field(None, description="Validation mode")
    pdfa_valid: Optional[bool] = Field(None, description="PDF/A-3b validation result (null if the layer did not run or did not apply)")
    validation_completeness: str = Field(default="full", description="full if all applicable layers ran, partial if some were skipped")
    layers_executed: List[str] = Field(default_factory=list, description="Validation layers that actually ran (xsd, schematron, pdfa3b, br_fr_ctc)")
    layers_skipped: List[SkippedLayer] = Field(default_factory=list, description="Validation layers that were skipped with reasons")
    pro_hint: Optional[ProHint] = Field(None, description="Optional enhanced-diagnostics summary in enabled builds")


class DiagnosticDetail(BaseModel):
    """A single diagnostic with a human-readable explanation."""
    rule_id: str = Field(..., description="EN 16931 rule ID (e.g., BR-CO-10)")
    severity: str = Field(..., description="Severity: error, warning, info")
    title: str = Field(..., description="Short, actionable title")
    explanation: str = Field(..., description="Detailed explanation of the issue")
    suggestion: str = Field(..., description="How to fix this issue")
    context: Optional[Dict[str, Any]] = Field(None, description="Extracted values for debugging")


class ProValidationResult(BaseModel):
    """Historical licensed response with enhanced diagnostics."""
    valid: bool = Field(..., description="Whether the file is valid")
    format: Optional[str] = Field(None, description="Detected format")
    flavor: Optional[str] = Field(None, description="Detected profile")
    error_count: int = Field(..., description="Total number of errors")
    warning_count: int = Field(default=0, description="Total number of warnings")
    diagnostics: List[DiagnosticDetail] = Field(default_factory=list, description="Smart diagnostics with explanations")
    validation_mode: str = Field(default="pro_diagnostics", description="Always 'pro_diagnostics' for this response type")
    pdfa_valid: Optional[bool] = Field(None, description="PDF/A-3b validation result (null if the layer did not run or did not apply)")
    validation_completeness: str = Field(default="full", description="full if all applicable layers ran, partial if some were skipped")
    layers_executed: List[str] = Field(default_factory=list, description="Validation layers that actually ran")
    layers_skipped: List[SkippedLayer] = Field(default_factory=list, description="Validation layers that were skipped with reasons")


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str = Field(..., description="Error type/code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[dict] = Field(None, description="Additional error details")
