import pytest

from app.schemas.validation import (
    BuyerInfo,
    InvoiceMetadata,
    LineItem,
    MonetaryAmounts,
    SellerInfo,
)


def test_strict_tolerance_rejection():
    """Reject a 0.05 totals mismatch before generating XML."""

    with pytest.raises(ValueError, match="grand_total"):
        InvoiceMetadata(
            invoice_number="AUDIT-TOLERANCE-001",
            issue_date="20260126",
            seller=SellerInfo(
                name="Strict Seller",
                address={"line1": "Rue de la Loi", "postcode": "75000", "city": "Paris", "country_code": "FR"},
                siret="12345678900010",
            ),
            buyer=BuyerInfo(
                name="Strict Buyer",
                address={"line1": "Rue Client", "postcode": "69000", "city": "Lyon", "country_code": "FR"},
            ),
            lines=[
                LineItem(
                    name="Item 1",
                    quantity=1.0,
                    net_price=100.00,
                    net_total=100.00,
                    vat_rate=20.00,
                    vat_category="S",
                )
            ],
            tax_details=[
                {"calculated_amount": "20.00", "basis_amount": "100.00", "rate": "20.00", "category_code": "S"}
            ],
            amounts=MonetaryAmounts(
                tax_basis_total="100.00",
                tax_total="20.00",
                grand_total="120.05",
                due_payable="120.05",
            ),
            currency_code="EUR",
            profile="en16931",
        )

if __name__ == "__main__":
    test_strict_tolerance_rejection()
