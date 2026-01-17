"""
Pydantic models for API request/response validation.
"""
from typing import Optional, Literal
from pydantic import BaseModel, Field


class SellerInfo(BaseModel):
    """Seller (Supplier) information."""
    name: str = Field(..., description="Seller company name")
    country_code: str = Field(..., description="ISO 3166-1 alpha-2 country code", min_length=2, max_length=2)
    tax_number: Optional[str] = Field(None, description="Tax number (FC scheme)")
    vat_number: Optional[str] = Field(None, description="VAT identification number (VA scheme)")


class BuyerInfo(BaseModel):
    """Buyer (Customer) information."""
    name: str = Field(..., description="Buyer company name")


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
    amounts: MonetaryAmounts
    currency_code: str = Field(default="EUR", description="ISO 4217 currency code")
    profile: Literal["minimum", "basicwl", "basic", "en16931", "extended"] = Field(
        default="minimum",
        description="Factur-X profile level"
    )
    document_type_code: str = Field(default="380", description="Document type code (380=Commercial Invoice)")


class ValidationResult(BaseModel):
    """Validation result response."""
    valid: bool = Field(..., description="Whether the file is valid")
    format: Optional[str] = Field(None, description="Detected format (factur-x, zugferd, order-x)")
    flavor: Optional[str] = Field(None, description="Detected flavor/level")
    errors: list[str] = Field(default_factory=list, description="List of validation errors")


class ErrorResponse(BaseModel):
    """Standard error response."""
    error: str = Field(..., description="Error type/code")
    message: str = Field(..., description="Human-readable error message")
    details: Optional[dict] = Field(None, description="Additional error details")
