# Factur-X Engine (Community Edition)

[![View Source](https://img.shields.io/badge/View_Source_Code-GitHub-181717?style=for-the-badge&logo=github)](https://github.com/facturx-engine/facturx-engine)
[![Docker Pulls](https://img.shields.io/docker/pulls/facturxengine/facturx-engine?style=for-the-badge)](https://hub.docker.com/r/facturxengine/facturx-engine)
[![License](https://img.shields.io/badge/License-Community-0052CC?style=for-the-badge)](https://github.com/facturx-engine/facturx-engine#legal)
[![Standard](https://img.shields.io/badge/Standard-EN16931-2EA44F?style=for-the-badge)](https://fnfe-mpe.org/factur-x/)
[![CRA](https://img.shields.io/badge/EU_CRA-Compliant-blueviolet?style=for-the-badge)](https://github.com/facturx-engine/facturx-engine/blob/main/_INTERNAL/docs/CRA_COMPLIANCE.md)

**The simplest self-hosted Docker Middleware to generate compliant Factur-X (French E-Invoicing) and ZUGFeRD 2.2 PDFs.**
Turn standard PDFs into valid Hybrid Invoices (PDF/A-3 + XML) via a simple REST API.

---

## 🇪🇺 Trust & Sovereignty (GDPR)

In the era of the **Cyber Resilience Act (CRA)** and strict **GDPR** enforcement, Factur-X Engine is designed as a "Privacy-First" component.

### 🔒 100% Offline & Private (GDPR-by-Design)

* **Zero Data Exfiltration**: The container runs without *any* outbound internet connection. Your invoices (and your clients' data) never leave your infrastructure.
* **Stateless Processing**: Data is processed in RAM and discarded immediately. No databases, no logs of sensitive content.
* **Sovereign**: Ideal for Banks, Healthcare, and Public Sector entities requiring strict data locality.

### 🛡️ Security & Compliance

* **CRA Ready**: We provide a full "Security by Design" compliance statement and vulnerability management process.
* **SBOM Included**: Every release comes with a **Software Bill of Materials** (CycloneDX) for your CISO's peace of mind.
* **Read-Only Architecture**: The engine works perfectly with read-only filesystems to prevent malware persistence.

---

## ⚡ Why Factur-X Engine?

## 📋 Technical Specs

* **Input**: Standard PDF (1.4+), any size.
* **Output**: PDF/A-3 compliant file with embedded `factur-x.xml`.
* **Profiles**: `MINIMUM`, `BASIC`, `BASIC WL`, `EN 16931` (Standard), `EXTENDED`.
* **Validation**: Returns a detailed JSON report (Format, Flavor, and list of errors).

## 🏗️ Architecture

### 1. Generation (Community Edition)

Turn any PDF into a Factur-X file in one API call.

```text
[Input PDF] + [JSON Metadata]
       ⬇️ POST /convert
┌──────────────────────────────┐
│      Factur-X Engine         │
│  (Merge PDF + Embedded XML)  │
└──────────────────────────────┘
       ⬇️ Returns
   [Factur-X PDF]
   (PDF/A-3 + XML)
```

### 2. Extraction (Pro Feature)

Parse incoming invoices accurately.

```text
   [Factur-X PDF]
       ⬇️ POST /extract
┌──────────────────────────────┐
│    Factur-X Engine Pro       │
│  (Read XML & Vendor Data)    │
└──────────────────────────────┘
       ⬇️ Returns
      [JSON Data]
 (Unmasked, Ready for ERP)
```

## 🚀 Features

* **PDF to Factur-X**: Embeds the required XML metadata into your existing PDF layouts.
* **Validation API**: Check your existing invoices against strict schema rules (XSD + Schematron).
* **Data Extraction**: Parse incoming Factur-X invoices to JSON (Demo Mode in Community, Full in Pro).
* **Standards Support**: Supports profiles `MINIMUM`, `BASIC`, `BASIC WL`, and `EN 16931`.
* **Dev-Friendly**: Swagger UI documentation and JSON Validation reports.

## 📦 Quick Start

Run the container in 1 command:

```bash
docker run -p 8000:8000 facturxengine/facturx-engine:latest
```

👉 Open **[http://localhost:8000/docs](http://localhost:8000/docs)** to see the Swagger UI.

### 1. Generate an Invoice

Send your PDF and metadata to the API.
See `/docs` for full JSON schema properties.

```bash
curl -X 'POST' \
  'http://localhost:8000/v1/convert' \
  -F 'pdf=@invoice.pdf' \
  -F 'metadata={
    "invoice_number": "INV-2024-001",
    "issue_date": "20240117",
    "seller": {"name": "My Corp", "country_code": "FR", "vat_number": "FR123456789"},
    "buyer": {"name": "Client SAS"},
    "amounts": {"tax_basis_total": "100.00", "tax_total": "20.00", "grand_total": "120.00", "due_payable": "120.00"},
    "profile": "en16931"
  }' \
  --output factur-x_invoice.pdf
```

### 2. Validate an Invoice

Check if a file complies with the standard:

```bash
curl -X 'POST' \
  'http://localhost:8000/v1/validate' \
  -F 'file=@factur-x_invoice.pdf'
```

### 3. Extract Data (Demo Mode)

Test the powerful OCR-free extraction (returns masked numbers in Community Edition):

```bash
curl -X POST "http://localhost:8000/v1/extract" \
  -F "file=@factur-x.pdf"
# Returns JSON with masked values (e.g. "total": "***.00")
```

---

## 💼 Free vs Pro

| Feature | Community Edition 🆓 | Pro Edition 💎 |
| :--- | :---: | :---: |
| **Generation** (PDF to Factur-X) | ✅ Unlimited | ✅ Unlimited |
| **Validation** (Compliance Check) | ✅ Unlimited | ✅ Unlimited |
| **Extraction** (Factur-X to JSON) | ⚠️ **Demo Mode** (Masked Data) | ✅ **Full Data Access** |
| **License** | Community (Free) | Commercial / Production |

### Upgrade to Pro

Need to **EXTRACT** real data from incoming supplier invoices for your ERP/Accounting software?
The Community Edition masks sensitive values (e.g., `TOTAL` becomes `***`).

**Get Factur-X Engine Pro to unlock:**

* 💎 **Full JSON Data Extraction** (OCR-free, 100% accuracy).
* 💎 **Production License** (Unlimited commercial use).
* 💎 **Priority Support**.
* 💎 **Security Updates** (SLA on patches).

**Contact:** [facturx.engine@protonmail.com](mailto:facturx.engine@protonmail.com)

👉 **[Get Factur-X Engine Pro](https://facturx-engine.lemonsqueezy.com)**

---

## 🏷️ Keywords

*Factur-X, ZUGFeRD, Chorus Pro, PDP, PPF, E-Invoicing, Facture Electronique, EN 16931, PDF/A-3, Python, Docker, API, Microservice, Offline, Odoo, Compliance.*
