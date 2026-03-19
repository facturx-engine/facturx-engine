from typing import Any, Dict, List, Optional

from pydantic import BaseModel


class ErrorDetail(BaseModel):
    code: str
    message: str

class Seller(BaseModel):
    name: Optional[str] = None
    registration_id: Optional[str] = None
    email: Optional[str] = None
    line1: Optional[str] = None
    city: Optional[str] = None
    postcode: Optional[str] = None
    country: Optional[str] = None
    vat_number: Optional[str] = None

class Buyer(BaseModel):
    name: Optional[str] = None
    registration_id: Optional[str] = None
    email: Optional[str] = None
    line1: Optional[str] = None
    city: Optional[str] = None
    postcode: Optional[str] = None
    country: Optional[str] = None
    vat_number: Optional[str] = None

class Totals(BaseModel):
    net_amount: Optional[str] = None
    tax_amount: Optional[str] = None
    gross_amount: Optional[str] = None
    payable_amount: Optional[str] = None

class LineItem(BaseModel):
    description: Optional[str] = None
    quantity: Optional[str] = None
    unit_code: Optional[str] = None
    unit_price: Optional[str] = None
    vat_rate: Optional[str] = None
    line_total: Optional[str] = None

class TaxBreakdownItem(BaseModel):
    category: Optional[str] = None
    vat_rate: Optional[str] = None
    basis_amount: Optional[str] = None
    tax_amount: Optional[str] = None

class InvoiceJson(BaseModel):
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None
    due_date: Optional[str] = None
    document_type_code: Optional[str] = None
    currency: Optional[str] = None
    buyer_reference: Optional[str] = None
    contract_reference: Optional[str] = None
    seller: Optional[Seller] = None
    buyer: Optional[Buyer] = None
    totals: Optional[Totals] = None
    tax_breakdown: List[TaxBreakdownItem] = []
    line_items: List[LineItem] = []
    _demo_mode: bool = False
    _license_notice: Optional[str] = None
    _meta: Optional[Dict[str, Any]] = None  # To support Community Edition extra comments
    
    model_config = {
        'populate_by_name': True,
        'extra': 'allow'
    }

class ExtractionResult(BaseModel):
    format_detected: Optional[str] = None
    profile_detected: Optional[str] = None
    xml_extracted: bool
    invoice_json: Optional[InvoiceJson] = None
    errors: List[ErrorDetail] = []
