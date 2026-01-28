"""
Pydantic models for API request/response validation.
"""
from typing import Optional, Literal, List
from pydantic import BaseModel, Field


class Address(BaseModel):
    """Physical address."""
    line1: str = Field(..., description="Main address line")
    line2: Optional[str] = Field(None, description="Additional address line")
    postcode: str = Field(..., description="Postal code")
    city: str = Field(..., description="City name")
    country_code: str = Field(..., description="ISO 3166-1 alpha-2 country code")


class SellerInfo(BaseModel):
    """Seller (Supplier) information."""
    name: str = Field(..., description="Seller company name")
    address: Optional[Address] = Field(None, description="Physical address (Mandatory for EN16931)")
    tax_number: Optional[str] = Field(None, description="Tax number (FC scheme)")
    vat_number: Optional[str] = Field(None, description="VAT identification number (VA scheme)")
    siret: Optional[str] = Field(None, description="SIRET (France specific)")


class BuyerInfo(BaseModel):
    """Buyer (Customer) information."""
    name: str = Field(..., description="Buyer company name")
    address: Optional[Address] = Field(None, description="Physical address")
    vat_number: Optional[str] = Field(None, description="VAT identification number")


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


class MonetaryAmounts(BaseModel):
    """Monetary summary amounts."""
    tax_basis_total: str = Field(..., description="Total amount excluding VAT")
    tax_total: str = Field(..., description="Total VAT amount")
    grand_total: str = Field(..., description="Total amount including VAT")
    due_payable: str = Field(..., description="Amount due for payment")


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
    document_type_code: str = Field(default="380", description="Document type code (380=Commercial Invoice)")


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
