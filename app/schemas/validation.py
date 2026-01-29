"""
Pydantic models for API request/response validation.
"""
from typing import Optional, Literal, List, Union
from pydantic import BaseModel, Field


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
    siret: Optional[str] = Field(None, description="SIRET (France specific)")
    global_id: Optional[str] = Field(None, description="Global Identifier (e.g. DUNS, GLN)")
    global_id_scheme: Optional[str] = Field(None, description="Scheme ID for Global ID (default: 0088 for GLN)")
    contact_name: Optional[str] = Field(None, description="Contact person name")
    phone: Optional[str] = Field(None, description="Phone number")
    email: Optional[str] = Field(None, description="Email address")
    iban: Optional[str] = Field(None, description="IBAN (Seller only)")
    bic: Optional[str] = Field(None, description="BIC (Seller only)")
    bank_name: Optional[str] = Field(None, description="Bank Name (Seller only)")


class BuyerInfo(BaseModel):
    """Buyer (Customer) information."""
    name: str = Field(..., description="Buyer company name")
    address: Optional[Address] = Field(None, description="Physical address")
    vat_number: Optional[str] = Field(None, description="VAT identification number")
    global_id: Optional[str] = Field(None, description="Global Identifier")
    global_id_scheme: Optional[str] = Field(None, description="Scheme ID for Global ID")
    contact_name: Optional[str] = Field(None, description="Contact person name")
    phone: Optional[str] = Field(None, description="Phone number")
    email: Optional[str] = Field(None, description="Email address")


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
    profile: Literal["minimum", "basicwl", "basic", "en16931", "extended"] = Field(
        default="en16931",
        description="Factur-X profile level"
    )
    due_date: Optional[str] = Field(None, description="Payment due date (YYYYMMDD format)")
    payment_terms: Optional[str] = Field(None, description="Payment terms description")
    document_type_code: str = Field(default="380", description="Document type code (380=Commercial Invoice)")
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


class ValidationResult(BaseModel):
    """Validation result response."""
    valid: bool = Field(..., description="Whether the file is valid")
    format: Optional[str] = Field(None, description="Detected format (factur-x, zugferd, order-x)")
    flavor: Optional[str] = Field(None, description="Detected flavor/level")
    errors: list[str] = Field(default_factory=list, description="List of validation errors")
    validation_mode: Optional[str] = Field(None, description="Validation mode: 'hybrid' (Pro) or 'lite' (Community)")


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str = Field(..., description="Error type/code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[dict] = Field(None, description="Additional error details")
