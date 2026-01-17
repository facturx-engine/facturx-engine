from pydantic import BaseModel
from typing import List, Optional, Any, Dict

class ErrorDetail(BaseModel):
    code: str
    message: str

class Seller(BaseModel):
    name: Optional[str] = None
    country: Optional[str] = None
    vat_number: Optional[str] = None

class Buyer(BaseModel):
    name: Optional[str] = None

class Totals(BaseModel):
    net_amount: Optional[str] = None
    tax_amount: Optional[str] = None
    gross_amount: Optional[str] = None
    payable_amount: Optional[str] = None

class LineItem(BaseModel):
    description: Optional[str] = None
    quantity: Optional[str] = None
    unit_price: Optional[str] = None
    line_total: Optional[str] = None

class InvoiceJson(BaseModel):
    invoice_number: Optional[str] = None
    invoice_date: Optional[str] = None
    document_type_code: Optional[str] = None
    currency: Optional[str] = None
    seller: Optional[Seller] = None
    buyer: Optional[Buyer] = None
    totals: Optional[Totals] = None
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
