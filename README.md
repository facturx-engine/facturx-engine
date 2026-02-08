# Factur-X Engine

> **The Privacy-First Invoicing Engine.** 100% Air-gapped, Official SaxonC Validation (Chorus Pro / KoSIT Parity). Generate and Validate Factur-X, ZUGFeRD 2.x, and XRechnung 3.0 without cloud dependencies.

![Docker Pulls](https://img.shields.io/docker/pulls/facturxengine/facturx-engine) [![GitHub](https://img.shields.io/badge/github-repo-181717?logo=github)](https://github.com/facturx-engine/facturx-engine) ![License](https://img.shields.io/badge/license-Community-blue.svg) ![Standard](https://img.shields.io/badge/standard-EN16931-green.svg) [![CRA](https://img.shields.io/badge/EU_CRA-Ready-blueviolet)](docs/cra.md)
![Privacy First](https://img.shields.io/badge/Privacy-Air_Gapped-success?logo=shield-dog) ![SaxonC](https://img.shields.io/badge/Powered_By-SaxonC_HE-blue)
![Image Size](https://img.shields.io/docker/image-size/facturxengine/facturx-engine/latest) ![Compliance](https://img.shields.io/badge/Compliance-Factur--X%20%2F%20ZUGFeRD-blue) ![Security](https://img.shields.io/badge/Security-SBOM%20Available-success)

---

## Use Cases

> **The standard for secure e-invoicing.** Generate and Validate Factur-X / ZUGFeRD 2.2 / XRechnung 3.0 files.

* **Community Edition (Free & Unlimited)**: Full validation (XSD + Official Schematron) and Factur-X generation. **No quotas, no external calls.** Ideal for Dev, Test, and CI/CD.
* **Pro Edition**: **Smart Diagnostics** (Translates cryptic `BR-CO-10` errors into human instructions), **Business-Ready Extraction** (Flat JSON for ERPs), and **Advanced "Angles Morts" Detection** (SIRET/VAT mismatch, Auto-Avoir).
* **Trial Mode**: All Pro features are automatically unlocked when using the provided [reference files](tests/corpus/valid/).
* **France 2026 Mandate (PDP/PPF)**: Generate compliant invoices for the upcoming French electronic invoicing mandate.
* **Germany 2025 Mandate (B2B)**: Full support for the upcoming German mandate requiring electronic invoices from January 2025.
* **Official Validation (SaxonC)**: Verify files against EN 16931 Schematron rules using the same engine as official portals (Chorus Pro / KoSIT).
* **International Standards**: Support for Factur-X, ZUGFeRD 2.2, and XRechnung 3.0 (CII/UBL).
* **Security & Compliance**: Strictly Air-gapped / offline execution. No external calls, rules are embedded. Designed for GDPR and sovereign environments.

[REST API Reference](https://facturx-engine.github.io/facturx-engine/ref/api-reference.html) | [OpenAPI Spec (JSON)](docs/openapi.json) | [OpenAPI (Raw JSON)](https://raw.githubusercontent.com/facturx-engine/facturx-engine/main/docs/openapi.json) | [Integration Recipes](https://facturx-engine.github.io/facturx-engine/) | [Troubleshooting](https://facturx-engine.github.io/facturx-engine/guides/error-codes.html)

---

## Compliance & Privacy (GDPR / DORA)

**Target: Enterprise, SaaS, and Regulated Industries.**

In a landscape of data breaches and strict regulations, Factur-X Engine offers a "Privacy-First" architecture:

* **Zero Third-Party Dependency**: Runs **entirely on your infrastructure**. You own the runtime.
* **Data Sovereignty (GDPR)**: 100% **Air-Gapped**. No financial data ever leaves your secure network.
* **Operational Resilience (DORA)**: In case of global internet outage, your ability to issue invoices remains intact.

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

# Windows PowerShell
$metadata = Get-Content examples\simple_invoice.json -Raw
curl.exe -X POST "http://localhost:8000/v1/convert" `
  -F "pdf=@examples/invoice_raw.pdf" `
  -F "metadata=$metadata" `
  --output invoice_compliant.pdf
```

### 3. Generate Raw XML (Headless / API-First)

Directly generate the **Cross Industry Invoice (CII)** XML without creating a PDF. Ideal for backend integrations where you only need the structured data.

```bash
# Linux/macOS
curl -X POST "http://localhost:8000/v1/xml" \
  -F "metadata=$(cat examples/simple_invoice.json)" \
  --output factur-x.xml

# Windows PowerShell
$metadata = Get-Content examples\simple_invoice.json -Raw
curl.exe -X POST "http://localhost:8000/v1/xml" `
  -F "metadata=$metadata" `
  --output factur-x.xml
```

### 4. Extract to JSON (Open Core)

The Community Edition extracts **full financial and identity data**. No masking, no obfuscation.

```bash
# Transform a Supplier Invoice (PDF) into Actionable JSON
curl -X POST "http://localhost:8000/v1/extract" \
  -F "file=@supplier_invoice.pdf"
```

**Response Preview (Business-Ready):**

```json
{
  "invoice_number": "INV-2024-001",
  "issue_date": "2024-10-05",
  "seller": { 
      "name": "Acme Corp",
      "siret": "12345678900012",
      "vat_number": "FR12345678901"
  },
  "totals": { 
      "net_amount": 1500.00, 
      "tax_amount": 300.00,
      "total_amount": 1800.00
  },
  "payment": {
      "iban": "FR76...",
      "due_date": "2024-11-05"
  }
}
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

The engine uses **SaxonC-HE**, ensuring technical parity with state-level platforms such as **Chorus Pro / PPF (France)** and **KoSIT (Germany)**. It executes official **EN 16931 Schematron** business rules.

> [!IMPORTANT]
> **Technical Parity**: By using the official SaxonC engine internally, Factur-X Engine ensures that an invoice passing validation here will be technically accepted by national portals. This eliminates the "validation gap" common with unofficial open-source parsers.

* **Community (Teaser)**: Returns the first validation error found.
* **Pro (Full Compliance)**: Returns the complete compliance report (JSON). Use this for automated quality gates and error-mapping in ERP systems.

```bash
# Linux/macOS
curl -X POST "http://localhost:8000/v1/validate" -F "file=@invoice_compliant.pdf"

# Windows PowerShell
curl.exe -X POST "http://localhost:8000/v1/validate" -F "file=@invoice_compliant.pdf"
```

### 6. File Compatibility

| Endpoint | Input Formats | Output Formats |
| :--- | :--- | :--- |
| `/v1/convert` | PDF (v1.4+) + JSON | **Factur-X** (PDF/A-3 + XML) |
| `/v1/validate` | PDF/A-3, XML (CII/UBL) | JSON Report |
| `/v1/extract` | Factur-X PDF | JSON Data + XML |
| `/v1/xml` | JSON | XML (CII) |
| `/v1/serialize` | PDF, XML | Business-Ready JSON |

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

**CORS Note**: CORS is enabled by default (`CORS_ORIGINS=*`). Headers appear on POST/OPTIONS responses but may not be visible in simple GET requests.

---

## Community vs Pro

This **Community** version is production-ready. The code is Open Core (transparent Python).

| Feature | Community Edition | Pro / Enterprise Edition |
| :--- | :--- | :--- |
| **License** | FSL 1.1 (Free for non-competing use) | Commercial (SLA & Priority) |
| **Extraction** | **Full Data** | **Business-Ready JSON** (Flattened/Typed) |
| **Validation** | **Full EN 16931 rules** | **Smart Diagnostics** (Human Suggestions) |
| **Metrics** | **Basic** (Ops) | **Full** (Business) |
| **Support** | Community | Priority / SLA |

### Try Pro Features for Free

Upload one of our official reference files to unlock **all Pro features** without a license:

**For Smart Diagnostics:**

* Use files from `tests/corpus/invalid/` to see human-readable error explanations instead of cryptic rule IDs

**For Business-Ready Serialization:**

* Use files from `tests/corpus/valid/` to extract structured JSON from compliant invoices

The engine recognizes these files via MD5 hash and automatically enables Trial Mode.

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
