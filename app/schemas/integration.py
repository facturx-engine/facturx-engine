"""Strict, versioned response models for inbound invoice normalization."""

from datetime import date
from decimal import Decimal
from typing import List, Literal, Optional

from pydantic import BaseModel, Field


class AddressSchema(BaseModel):
    """Postal address as represented in the source invoice.

    Optional source values stay null. The engine never fabricates address data.
    """

    line1: Optional[str] = None
    line2: Optional[str] = None
    city: Optional[str] = None
    postcode: Optional[str] = None
    country_code: Optional[str] = Field(
        default=None,
        description="ISO 3166-1 alpha-2 code when present in the source document",
    )


class PartySchema(BaseModel):
    """Normalized seller or buyer data copied from the source invoice."""

    name: str = Field(..., description="Party name from the source document")
    vat_number: Optional[str] = None
    registration_id: Optional[str] = None
    electronic_address: Optional[str] = None
    electronic_address_scheme: Optional[str] = None
    address: Optional[AddressSchema] = None
    email: Optional[str] = None


class LineItemSchema(BaseModel):
    """Normalized invoice line without inferred accounting values."""

    line_id: Optional[str] = None
    name: str
    description: Optional[str] = None
    quantity: Decimal
    unit_code: str = Field(..., description="UN/ECE Rec 20 unit code from the source")
    net_price: Decimal
    line_total: Decimal
    vat_rate: Decimal
    vat_category: str
    seller_assigned_id: Optional[str] = None
    buyer_assigned_id: Optional[str] = None


class TaxBreakdownSchema(BaseModel):
    """Tax subtotal copied from the source invoice."""

    category: str
    rate: Decimal
    basis_amount: Decimal
    tax_amount: Decimal


class BusinessReadyInvoice(BaseModel):
    """Normalized invoice contract produced only after a complete strict mapping."""

    invoice_number: str
    document_type_code: str
    invoice_date: date
    due_date: Optional[date] = None
    currency: str

    buyer_reference: Optional[str] = None
    purchase_order_reference: Optional[str] = None
    contract_reference: Optional[str] = None
    preceding_invoice_reference: Optional[str] = None

    payment_means_code: Optional[str] = None
    payment_reference: Optional[str] = None
    iban: Optional[str] = None

    seller: PartySchema
    buyer: PartySchema
    line_items: List[LineItemSchema]
    tax_breakdown: List[TaxBreakdownSchema]

    total_net_amount: Decimal
    total_tax_amount: Decimal
    total_gross_amount: Decimal
    amount_due: Decimal

    format: Literal["cii", "ubl"]
    profile: Optional[str] = Field(
        default=None,
        description="Detected profile when it can be derived from the source document",
    )


class SerializationDiagnostic(BaseModel):
    """Stable machine-readable diagnostic for validation or mapping failures."""

    code: str
    message: str
    source: Literal["xml", "validation", "mapping", "invariant", "system"]
    path: Optional[str] = None
    severity: Literal["error", "warning"] = "error"


class SerializationResponse(BaseModel):
    """Successful strict serialization response.

    Success means that the configured validation layers passed and every material
    source value supported by this schema was mapped without recovery or defaults.
    It does not mean that an ERP may book or pay the invoice automatically.
    """

    success: Literal[True] = True
    schema_version: Literal["2.0.0"] = "2.0.0"
    engine_version: str
    execution_status: Literal["complete"] = "complete"
    mapping_status: Literal["complete"] = "complete"
    validation_status: Literal["passed"] = "passed"
    suggested_route: Literal["continue_client_checks"] = "continue_client_checks"
    invoice: BusinessReadyInvoice
    unmapped: List[dict[str, str]] = Field(default_factory=list)
    client_checks_required: List[str] = Field(
        default_factory=lambda: [
            "supplier_master_match",
            "duplicate_invoice_check",
            "purchase_order_match",
            "tax_policy_check",
            "payment_approval",
        ]
    )


class SerializationFailureResponse(BaseModel):
    """HTTP 422 response for input that cannot produce the strict contract."""

    success: Literal[False] = False
    schema_version: Literal["2.0.0"] = "2.0.0"
    engine_version: str
    execution_status: Literal["complete", "failed"]
    mapping_status: Literal["not_started", "failed"]
    validation_status: Literal["not_run", "rejected", "incomplete", "passed"]
    suggested_route: Literal["manual_review", "reject_input"]
    errors: List[SerializationDiagnostic]
