"""
Business-Ready JSON schemas for Factur-X/ZUGFeRD Extraction.
Designed for ERP integration and automated accounting.
"""
from pydantic import BaseModel, Field
from typing import List, Optional, Dict
from decimal import Decimal
from datetime import date


class AddressSchema(BaseModel):
    """Normalized physical address."""
    line1: str
    line2: Optional[str] = None
    city: str
    postcode: str
    country_code: str  # ISO 3166-1 alpha-2


class PartySchema(BaseModel):
    """Normalized party (Seller/Buyer) representation."""
    name: str = Field(..., description="Legal company name")
    vat_number: Optional[str] = Field(None, description="VAT ID with country prefix")
    registration_id: Optional[str] = Field(None, description="Trade registration number")
    address: Optional[AddressSchema] = None
    email: Optional[str] = None


class LineItemSchema(BaseModel):
    """High-precision invoice line item."""
    name: str
    description: Optional[str] = None
    quantity: Decimal
    unit_code: str = Field(..., description="UN/ECE Rec 20 unit code (e.g., C62, HUR)")
    unit_label: Optional[str] = Field(None, description="Human readable unit (e.g., piece, hour)")
    net_price: Decimal = Field(..., description="Net unit price")
    line_total: Decimal = Field(..., description="Net line total (Qty * Price)")
    vat_rate: Decimal = Field(..., description="VAT percentage (e.g., 20.00)")
    vat_category: str = Field(default="S", description="VAT category code (EN 16931)")


class TaxBreakdownSchema(BaseModel):
    """Normalized tax breakdown per category/rate."""
    category: str
    rate: Decimal
    basis_amount: Decimal
    tax_amount: Decimal


class BusinessReadyInvoice(BaseModel):
    """
    The 'Killer Feature' Pro Schema.
    Flattened, typed, and normalized for direct ERP consumption.
    """
    invoice_number: str
    invoice_date: date
    due_date: Optional[date] = None
    currency: str = Field(default="EUR")
    
    seller: PartySchema
    buyer: PartySchema
    
    line_items: List[LineItemSchema]
    tax_breakdown: List[TaxBreakdownSchema]
    
    # Financial Totals (Decimal precision)
    total_net_amount: Decimal
    total_tax_amount: Decimal
    total_gross_amount: Decimal
    amount_due: Decimal
    
    # Metadata
    format: str = Field(..., description="factur-x / zugferd / xrechnung")
    profile: str = Field(..., description="minimum / basic / en16931 / extended")
    is_obfuscated: bool = Field(default=False, description="True if data is masked for trial users")


class SerializationResponse(BaseModel):
    """Response model for the /serialize endpoint."""
    success: bool
    invoice: Optional[BusinessReadyInvoice] = None
    trial_notice: Optional[str] = None
    errors: List[Dict[str, str]] = []
