# Factur-X Engine

> **The Privacy-First Invoicing Engine.** 100% Air-gapped, Official SaxonC Validation. Generate & Validate Factur-X / ZUGFeRD 2.x without cloud dependencies.

![Docker Pulls](https://img.shields.io/docker/pulls/facturxengine/facturx-engine) [![GitHub](https://img.shields.io/badge/github-repo-181717?logo=github)](https://github.com/facturx-engine/facturx-engine) ![License](https://img.shields.io/badge/license-Community-blue.svg) ![Standard](https://img.shields.io/badge/standard-EN16931-green.svg) [![CRA](https://img.shields.io/badge/EU_CRA-Ready-blueviolet)](docs/cra.md)

---

## Use Cases

> **The standard for secure e-invoicing.** Generate and Validate Factur-X / ZUGFeRD 2.2 / XRechnung 3.0 files.

* **E-invoicing France 2026 (PDP/PPF)**: Generate compliant invoices for the upcoming French mandate.
* **EN 16931 Compliance**: Validate files against official **Schematron** rules using the embedded **SaxonC** engine.
* **International Standards**: Support for **Factur-X**, **ZUGFeRD 2.2**, and **XRechnung 3.0**.
* **Security & Compliance**: Strictly **Air-gapped** / offline execution. No external calls, rules are embedded. Ideal for GDPR and restricted environments.

[REST API Reference](https://facturx-engine.github.io/facturx-engine/ref/api-reference.html) | [OpenAPI Spec (JSON)](docs/openapi.json) | [OpenAPI (Raw JSON)](https://raw.githubusercontent.com/facturx-engine/facturx-engine/main/docs/openapi.json) | [Integration Recipes](https://facturx-engine.github.io/facturx-engine/) | [Troubleshooting](https://facturx-engine.github.io/facturx-engine/guides/error-codes.html)

---

## Quickstart

Runs immediately on any Docker host. No Python/Java dependencies.

### 1. Start the Engine (API)

```bash
docker run -d -p 8000:8000 --name facturx-engine facturxengine/facturx-engine:latest
```

### 2. Generate Factur-X (PDF + XML)

Merge a standard PDF with JSON data to create a compliant **Factur-X** (PDF/A-3) invoice.

```bash
# Linux/macOS
curl -X POST "http://localhost:8000/v1/convert" \
  -F "pdf=@examples/invoice_raw.pdf" \
  -F "metadata=$(cat examples/simple_invoice.json)" \
  --output invoice_compliant.pdf
```

### 3. Generate Raw XML (Headless / API-First)

Directly generate the **Cross Industry Invoice (CII)** XML without creating a PDF. Ideal for backend integrations where you only need the structured data.

```bash
curl -X POST "http://localhost:8000/v1/xml" \
  -F "metadata=$(cat examples/simple_invoice.json)" \
  --output factur-x.xml
```

### 4. Extract to JSON (Open Core)

The Community Edition extracts **full financial and identity data**. No masking, no obfuscation.

```bash
curl -X POST "http://localhost:8000/v1/extract" \
  -F "file=@invoice_compliant.pdf"
```

**Response Preview:**

```json
{
  "invoice_number": "INV-2024-001",
  "issue_date": "2024-10-05",
  "seller": { "name": "Acme Corp" },
  "totals": { "net_amount": "1500.00", "tax_amount": "300.00" }
}
```

### 5. Validation (Compliance Gate)

Protect your accounting system by verifying invoices **before** integration.

The engine uses **SaxonC-HE**, the same technology as **Chorus Pro / PPF (PDP)**, to run official **EN 16931 Schematron** rules.

* **Community (Teaser)**: Detects if the file is invalid. Returns the first error.
* **Pro (Official Engine)**: Returns the **full compliance report**. Use this to know exactly why a file would be rejected by the tax authority.

```bash
curl -X POST "http://localhost:8000/v1/validate" -F "file=@invoice_compliant.pdf"
```

### 6. File Compatibility

| Endpoint | Input Formats | Output Formats |
| :--- | :--- | :--- |
| `/v1/convert` | PDF (v1.4+) + JSON | **Factur-X** (PDF/A-3 + XML) |
| `/v1/validate` | PDF/A-3, XML (CII/UBL) | JSON Report |
| `/v1/extract` | Factur-X PDF | JSON Data + XML |
| `/v1/xml` | JSON | XML (CII) |

---

## Observability

Prometheus-compatible metrics endpoint.

```bash
curl http://localhost:8000/metrics
```

**Split Metrics Behavior:**

* **Community**: Basic operational metrics (uptime, request counts, latency).
* **Pro**: Full business metrics (validation outcomes, profile types, error rule IDs) tailored for business intelligence dashboards.

---

## Developer Integration

Factur-X Engine is designed to be language-agnostic.
**[View Integration Recipes (Python, Node, PHP)](https://facturx-engine.github.io/facturx-engine/#api)**

---

## Configuration

The container is configurable via environment variables:

| Variable | Description |
| :--- | :--- |
| `PORT` | API Listening Port (Default: 8000) |
| `LICENSE_KEY` | Pro License Key (Base64) |
| `WORKERS` | Number of Gunicorn Workers |

---

## Community vs Pro

This **Community** version is production-ready. The code is Open Core (transparent Python).

| Feature | Community Edition | Pro / Enterprise Edition |
| :--- | :--- | :--- |
| **License** | FSL 1.1 (Free for non-competing use) | Commercial (SLA & Indemnity) |
| **Extraction** | **Full Data** | **Full Data** |
| **Validation** | **Teaser Mode** (1 error) | **Official Engine** (SaxonC / Parity with Chorus Pro) |
| **Metrics** | **Basic** (Ops) | **Full** (Business) |
| **Support** | Community | Priority / SLA |

### Pricing & Licenses

**1. For Internal Use (SME / Bank / Corporate)**
**Standard License (499 € / year)**: Unlimited usage for your own company.

**2. For OEM & Integrators (SaaS / ERP)**
**OEM Growth (2 490 € / year)**: Commercial Redistribution. Standard Liability Terms.
**OEM Scale (Contact Us)**: Enterprise Redistribution. **Includes Legal Indemnification & Insurance**.

> **Perpetual Fallback**: You keep the version you bought forever. The subscription covers updates, security patches & warranty.

**[Get Pro License](https://facturx-engine.lemonsqueezy.com)**

---

## Legal Disclaimer & Limitation of Liability

> **IMPORTANT**: This software is a technical tool for data formatting. It does not replace professional tax advice.

**1. Verification Responsibility**
Factur-X Engine generates files according to technical standards (EN 16931). The user retains full responsibility for the fiscal accuracy, completeness, and veracity of the invoice data (VAT rates, mandatory mentions, exemptions).

**2. No Guarantee of Acceptance**
While we strive for technical compliance with official Schematron rules, the acceptance of an invoice by a platform (Chorus Pro, PPF, OZG-RE) depends on business rules and external factors beyond our control.

**3. Limitation of Liability**
**THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.** Use of the Community Edition is at your own risk.
For Commercial Licenses (Pro/Enterprise), liability is strictly limited to the technical availability terms defined in the Service Level Agreement (SLA). **We expressly exclude liability for indirect damages, including fiscal penalties or rejection of invoices.**

---

## Legal & Compliance

* **Vendor**: Factur-X Engine (Paris, France).
* **Compliance**: Designed to respect the EU **Cyber Resilience Act (CRA)**.
* **Security**: Image scanned (Trivy), SBOM (CycloneDX) included.

---

## FAQ

### Q: Does it require an internet connection?

**A:** No. The container is strictly **air-gapped** by design. It contains all necessary schemas (XSD) and Schematron rules (XSLT) internally.

### Q: Is it compliant with the 2026 French Reform (PDP) and German E-Rechnung?

**A:** Yes. It generates files strictly compliant with **EN 16931**, supporting both Factur-X (hybrid PDF) and XRechnung 3.0 (pure XML).

### Q: Why use a Docker container instead of a Python/PHP library?

**A:** PDF/A-3 conversion and Schematron validation require complex system dependencies (SaxonC, Ghostscript). Docker isolates this complexity, ensuring a stable **"Iso-Prod"** environment avoiding dependency conflicts.

---

*Maintained by the Factur-X Engine Team.*
