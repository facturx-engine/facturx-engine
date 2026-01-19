# 🔧 Fixing Factur-X Error: `BR-CO-09` (Seller VAT Identifier)

If your Factur-X / ZUGFeRD validation fails with the error code **`BR-CO-09`**, this guide is for you.

## 🔴 The Error

> **Rule ID:** `BR-CO-09`
> **Message:** *The Seller VAT identifier shall be provided if the Seller has a VAT identifier.*
> **XPath:** `rsm:SupplyChainTradeTransaction/ram:ApplicableHeaderTradeAgreement/ram:SellerTradeParty/ram:SpecifiedTaxRegistration/ram:ID`

### What it means

The standard (EN 16931) mandates that if your company (the Seller) acts within the EU, you **must** provide your VAT number (e.g., `FR123456789`). This is crucial for cross-border tax compliance.

---

## 🛠️ The Fix (Python / XML)

### Option 1: The "Hard Way" (lxml)

If you are building the XML manually using `lxml` or templates, you must ensure the `<ram:SpecifiedTaxRegistration>` tag exists inside `<ram:SellerTradeParty>`.

```python
# ❌ INCORRECT (Missing VAT)
seller = etree.SubElement(agreement, "ram:SellerTradeParty")
etree.SubElement(seller, "ram:Name").text = "My Company"

# ✅ CORRECT
seller = etree.SubElement(agreement, "ram:SellerTradeParty")
etree.SubElement(seller, "ram:Name").text = "My Company"

# Add the VAT ID (Scheme VA = VAT)
tax_reg = etree.SubElement(seller, "ram:SpecifiedTaxRegistration")
vat_id = etree.SubElement(tax_reg, "ram:ID")
vat_id.set("schemeID", "VA")
vat_id.text = "FR12345678901"
```

### Option 2: The "Easy Way" (Factur-X Engine)

Stop fighting with `lxml` and XML schemas. Use **Factur-X Engine** to handle the compliance logic for you.

You just pass the VAT number in the JSON metadata, and the engine places it in the correct XML node automatically.

```bash
curl -X POST "http://localhost:8000/v1/convert" \
  -F "pdf=@invoice.pdf" \
  -F "metadata={
    \"invoice_number\": \"INV-001\",
    \"seller\": {
      \"name\": \"My Company\", 
      \"country_code\": \"FR\", 
      \"vat_number\": \"FR12345678901\"  <-- PROBLEM SOLVED
    },
    \"buyer\": {\"name\": \"Client SAS\"},
    \"amounts\": {\"grand_total\": \"100.00\"}
  }" \
  -o compliant_invoice.pdf
```

### 💡 Why use the Engine?

* **Automatic Formatting**: It checks if the VAT format is plausible for the country code.
* **Schema Validation**: It runs the EN 16931 validators *after* generation to guarantee you never send an invalid invoice.

---

[🚀 **Try Factur-X Engine (Docker)**](https://github.com/facturx-engine/facturx-engine) | [📘 **View Documentation**](../../README.md)
