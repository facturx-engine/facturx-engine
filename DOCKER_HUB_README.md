# Factur-X Engine

> **The Privacy-First Invoicing Engine.** 100% Air-gapped, Official SaxonC Validation (Chorus Pro / KoSIT Parity). Generate and Validate Factur-X, ZUGFeRD 2.x, and XRechnung 3.0 without cloud dependencies.

[![Docker Pulls](https://img.shields.io/docker/pulls/facturxengine/facturx-engine)](https://hub.docker.com/r/facturxengine/facturx-engine) [![GitHub](https://img.shields.io/badge/github-repo-181717?logo=github)](https://github.com/facturx-engine/facturx-engine) ![License](https://img.shields.io/badge/license-Community-blue.svg) ![Standard](https://img.shields.io/badge/standard-EN16931-green.svg) [![CRA](https://img.shields.io/badge/EU_CRA-Ready-blueviolet)](https://github.com/facturx-engine/facturx-engine/blob/main/docs/cra.md)
![Privacy First](https://img.shields.io/badge/Privacy-Air_Gapped-success?logo=shield-dog) ![SaxonC](https://img.shields.io/badge/Powered_By-SaxonC_HE-blue)
![Image Size](https://img.shields.io/docker/image-size/facturxengine/facturx-engine/latest) ![Compliance](https://img.shields.io/badge/Compliance-Factur--X%20%2F%20ZUGFeRD-blue) ![Security](https://img.shields.io/badge/Security-SBOM%20Available-success)

---

## Use Cases

> **The standard for secure e-invoicing.** Generate and Validate Factur-X / ZUGFeRD 2.2 / XRechnung 3.0 files.

* **Community Edition (Free & Unlimited)**: Full validation (XSD + Official SaxonC/Schematron) and Factur-X generation. **No quotas, no external calls.** Ideal for Dev, Test, and CI/CD.
* **Pro Edition**: **Smart Diagnostics** (Translates cryptic `BR-CO-10` errors into human instructions), **Business-Ready Extraction** (Flat JSON for ERPs), and **Advanced "Angles Morts" Detection** (SIRET/VAT mismatch, Auto-Avoir).

## Quickstart

Runs immediately on any Docker host. No Python/Java dependencies.

### 1. Start the Engine (API)

```bash
docker run -d -p 8000:8000 --name facturx-engine facturxengine/facturx-engine:latest
```

### 2. Generate Factur-X (PDF + XML)

Merge a standard PDF with JSON data to create a compliant **Factur-X** (PDF/A-3) invoice.

```bash
curl -X POST "http://localhost:8000/v1/convert" \
  -F "pdf=@examples/invoice_raw.pdf" \
  -F "metadata=$(cat examples/simple_invoice.json)" \
  --output invoice_compliant.pdf

echo "Invoice generated: invoice_compliant.pdf"
```

### 3. Generate Raw XML (Headless / API-First)

Directly generate the **Cross Industry Invoice (CII)** XML without creating a PDF. Ideal for backend integrations where you only need the structured data.

```bash
curl -X POST "http://localhost:8000/v1/xml" \
  -F "metadata=$(cat examples/simple_invoice.json)" \
  --output factur-x.xml
```

### 4. Extract to JSON (Open Core)

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

### 5. Serialize to Business-Ready JSON (Pro)

Transform XML/PDF into a clean, flattened JSON format for ERP integration.

```bash
curl -X POST "http://localhost:8000/v1/serialize" \
  -F "file=@invoice_compliant.pdf"
```

**[Swagger UI Documentation](http://localhost:8000/docs)** : <http://localhost:8000/docs>

---

## Technical Specifications

* **Official SaxonC Validation**: Internal engine provides technical parity with **Chorus Pro (France)** and **KoSIT (Germany)** validation portals.
* **Mandate Readiness**: Compliant with **France 2026 (PDP/PPF)** and **Germany 2025** electronic invoicing requirements.
* **Standards Compliance**: Supports **Factur-X**, **ZUGFeRD 2.2**, and **XRechnung 3.0** (CII/UBL). Includes Native Schematron Rules.
* **Stateless Architecture**: Zero persistence. Input data is processed in-memory and discarded. Ideal for GDPR/Privacy.
* **Air-Gapped Ready**: 100% Offline execution. No outbound network requests required.
* **Structural Extraction**: Parses Factur-X XML into standard JSON for ERP integration.

---

## Compliance & Privacy (GDPR / DORA)

**Target: Enterprise, SaaS, and Regulated Industries.**

In a landscape of data breaches and strict regulations, Factur-X Engine offers a "Privacy-First" architecture:

* **Zero Third-Party Dependency**: Runs **entirely on your infrastructure**. You own the runtime.
* **Data Sovereignty (GDPR)**: 100% **Air-Gapped**. No financial data ever leaves your secure network.
* **Operational Resilience (DORA)**: In case of global internet outage, your ability to issue invoices remains intact.

---

## Use Cases & Integrations

The Docker architecture makes the tool agnostic to your programming language.
**[View Full Integration Guide (Python, Node, PHP, C#, Java)](https://github.com/facturx-engine/facturx-engine/blob/main/docs/INTEGRATION.md)**

### PHP (Symfony / Laravel)
>
> "Delegate PDF/A complexity to a dedicated microservice instead of overloading your PHP runtime with heavy system dependencies."

### Python (FastAPI / Django)
>
> "Use the Docker image to avoid library conflicts (lxml, reportlab) and ensure an iso-prod environment."

### Node.js / Go / .NET
>
> "Integrate e-invoicing via simple standard HTTP calls."

---

## Configuration

The container is configurable via environment variables:

| Variable | Description | Default |
| :--- | :--- | :--- |
| `PORT` | API Listening Port | `8000` |
| `LICENSE_KEY` | Pro License Key | |
| `WORKERS` | Number of Gunicorn Workers | `1` |
| `LOG_LEVEL` | Log Level (info, debug) | `info` |

---

## Community vs Pro

This **Community** version is production-ready.

| Feature | Community Edition | Pro / Enterprise Edition |
| :--- | :--- | :--- |
| **License** | FSL 1.1 (Free for non-competing use) | Commercial (SLA & Priority) |
| **Extraction** | **Full Data** | **Business-Ready JSON** (Flattened/Typed) |
| **Validation** | **Full EN 16931 rules** | **Smart Diagnostics** (Human Suggestions) |
| **Metrics** | **Basic** (Ops) | **Full** (Business) |
| **Support** | Community | Priority / SLA |

### Pricing & Licenses

#### 1. For Internal Use (SME / Bank / Corporate)

* **Standard License**: Unlimited usage for your own company.

#### 2. For OEM & Integrators (SaaS / ERP)

* **OEM Growth**: Commercial Redistribution. Standard Liability Terms.
* **OEM Scale (Contact Only)**: Enterprise Redistribution. **Includes Legal Indemnification & Insurance**.

> **Perpetual Fallback**: You keep the version you bought forever. The subscription covers updates, security patches & warranty.

**[View Pricing & Licenses](https://facturx-engine.lemonsqueezy.com)**

---

## Legal Disclaimer & Limitation of Liability

> **IMPORTANT**: This software is a technical tool for data formatting. It does not replace professional tax advice.

**1. Verification Responsibility**
Factur-X Engine generates files according to technical standards (EN 16931). The user retains full responsibility for the fiscal accuracy, completeness, and veracity of the invoice data (VAT rates, mandatory mentions, exemptions).

**2. No Guarantee of Acceptance**
While we strive for technical compliance with official Schematron rules, the acceptance of an invoice by a platform (Chorus Pro, PPF, OZG-RE) depends on business rules and external factors beyond our control.

**3. Limitation of Liability**
**THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND.** Use of the Community Edition is at your own risk.
For Commercial Licenses (Pro/Enterprise), liability is strictly limited to the technical availability terms defined in the Service Level Agreement (SLA). **We expressly exclude liability for indirect damages, including fiscal penalties or rejected invoices.**

---

## Legal & Compliance

* **Vendor**: Factur-X Engine (Paris, France).
* **Compliance**: Designed to respect the EU **Cyber Resilience Act (CRA)**.
* **Security**: Image scanned (Trivy), SBOM available.

*Maintained by the Factur-X Engine Team.*
<!-- CI Verified -->
