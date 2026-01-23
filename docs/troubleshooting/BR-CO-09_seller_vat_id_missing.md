# How to Fix Factur-X / ZUGFeRD Error: BR-CO-09 (Seller VAT ID)

> **Error Message**: *"The Seller VAT identifier (BT-31) shall be present if the Seller tax representative VAT identifier (BT-63) is not present."*

If you are generating **Factur-X (hybrid XML-PDF)** or **ZUGFeRD 2.2** invoices, you may encounter the business rule **BR-CO-09**. It is a common reason for rejection on portals like **Chorus Pro** (France) or **XRechnung** receivers (Germany).

This guide explains why this error happens and how to fix it using **Factur-X Engine**.

---

## What is BR-CO-09?

The standard **EN 16931** (governing European e-invoicing) has strict rules about tax identification.

**BR-CO-09** enforces that:

1. **If the Seller has a VAT number**, it MUST be provided (Tag `BT-31`).
2. **Unless** a Tax Representative is defined (Tag `BT-63`).

In simple terms: **"Who is paying the VAT? We need an ID."**

### Why it fails

Developers often confuse:

* `GlobalID` (SIRET, DUNS)
* `TaxID` (FC, 37...)
* `VATID` (The actual Intracommunity VAT number starting with FR, DE, IT...)

If your XML maps the VAT number to the wrong field (e.g., placing the VAT ID inside the `<GlobalID>` tag instead of `<TaxRegistration>` schema), the validator sees an empty VAT ID and triggers **BR-CO-09**.

---

## Manual Solution: Debugging XML

Here is what a valid XML snippet looks like for EN 16931. If you are building the XML manually (Jinja2, String concat), you must ensure this exact structure:

```xml
<ram:ApplicableHeaderTradeAgreement>
    <ram:SellerTradeParty>
        <!-- BT-31: The VAT ID MUST be here -->
        <ram:SpecifiedTaxRegistration>
            <ram:ID schemeID="VA">FR12345678901</ram:ID>
        </ram:SpecifiedTaxRegistration>
    </ram:SellerTradeParty>
</ram:ApplicableHeaderTradeAgreement>
```

**Common Mistakes:**

* Using `schemeID="FC"` instead of `schemeID="VA` (VAT).
* Forgetting the `<SpecifiedTaxRegistration>` block entirely.
* Typos in the VAT characters (spaces, dots).

---

## Automated Solution: Factur-X Engine

Instead of implementing XML schema definitions (XSD), utilize **Factur-X Engine**. It automatically places data in the correct XML tags based on standard rules.

### 1. Simple JSON Payload

Provide the `vat_number` in the `seller` object. The engine handles schema mapping.

```json
{
  "seller": {
    "name": "My Company SAS",
    "vat_number": "FR12345678901",  <-- Just put it here
    "country_code": "FR"
  },
  "buyer": { ... }
}
```

### 2. Generate the files

Run the Docker container (offline, standard):

```bash
docker run -d -p 8000:8000 facturxengine/facturx-engine
```

Call the API:

```bash
curl -X POST "http://localhost:8000/v1/convert" \
  -F "pdf=@invoice.pdf" \
  -F "metadata=@data.json" \
  --output result.pdf
```

### Result

The generic PDF is transformed into a **compliant PDF/A-3** file. The embedded XML is guaranteed to be valid against **EN 16931**, resolving `BR-CO-09`.

---

## Summary

| Method | Fix for BR-CO-09 | Time to Fix |
| :--- | :--- | :--- |
| **Manual XML** | Read spec, find Tag BT-31, map SchemeID | Hours |
| **Factur-X Engine** | Add `"vat_number"` to JSON | Seconds |

**[Get Factur-X Engine on Docker Hub](https://hub.docker.com/r/facturxengine/facturx-engine)**
