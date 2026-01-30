# Factur-X Engine v1.3.3 "License Gated Edition"

> **Self-hosted REST API to generate, validate, and extract Factur-X / ZUGFeRD 2.x (2.4) + XRechnung 3.x files.**

[![Docker Pulls](https://img.shields.io/docker/pulls/facturxengine/facturx-engine)](https://hub.docker.com/r/facturxengine/facturx-engine) [![GitHub](https://img.shields.io/badge/github-repo-181717?logo=github)](https://github.com/facturx-engine/facturx-engine) [![License](https://img.shields.io/badge/license-Community-blue.svg)](https://github.com/facturx-engine/facturx-engine) [![Standard](https://img.shields.io/badge/standard-EN16931-green.svg)](https://fnfe-mpe.org/factur-x/) [![CRA](https://img.shields.io/badge/EU_CRA-Ready-blueviolet)](https://github.com/facturx-engine/facturx-engine/blob/main/docs/cra.md) [![SBOM](https://img.shields.io/badge/SBOM-CycloneDX-informational)](https://github.com/facturx-engine/facturx-engine/actions) [![Signed](https://img.shields.io/badge/Image-Cosign_Signed-success)](https://github.com/sigstore/cosign)

---

## Quickstart

Runs immediately on any Docker host. No Python/Java dependencies.

```bash
# 1. Start the Engine (API)
docker run -d -p 8000:8000 --name facturx-engine facturxengine/facturx-engine:latest

# 2. Download example files (from GitHub)
curl -O https://raw.githubusercontent.com/facturx-engine/facturx-engine/main/examples/invoice_raw.pdf
curl -O https://raw.githubusercontent.com/facturx-engine/facturx-engine/main/examples/simple_invoice.json

### 2. Generate Factur-X (PDF + XML)

Merge a standard PDF with JSON data to create a compliant **Factur-X** (PDF/A-3) invoice.

```bash
curl -X POST "http://localhost:8000/v1/convert" \
  -F "pdf=@invoice_raw.pdf" \
  -F "metadata=$(cat simple_invoice.json)" \
  --output invoice_compliant.pdf

echo "Invoice generated: invoice_compliant.pdf"
```

### 3. Generate Raw XML (Headless / API-First)

Directly generate the **Cross Industry Invoice (CII)** XML without creating a PDF. Ideal for backend integrations where you only need the structured data.

```bash
curl -X POST "http://localhost:8000/v1/xml" \
  -F "metadata=$(cat simple_invoice.json)" \
  --output factur-x.xml
```

### Extract to JSON (Open Core)

```bash
curl -X POST "http://localhost:8000/v1/extract" \
  -F "pdf=@invoice_compliant.pdf"
```

**[Swagger UI Documentation](http://localhost:8000/docs)** : <http://localhost:8000/docs>

---

## Technical Specifications

High-performance compliance engine for **EN 16931**.

* **Native PDF/A-3 Conversion**: Internal engine handles ISO 19005-3 conformance. **No external Ghostscript dependency**.
* **Standards Compliance**: Validates against **EN 16931**, **ZUGFeRD 2.4**, and **XRechnung 3.0**. Includes Native Schematron Rules (Business Logic) for France (SIRET, VAT) and Germany (Tax ID).
* **Stateless Architecture**: Zero persistence. Input data is processed in-memory and discarded. Ideal for GDPR/Privacy.
* **Air-Gapped Ready**: 100% Offline execution. No outbound network requests required.
* **Structured Extraction**: Parses Factur-X XML into standard JSON for ERP integration.

---

## Use Cases & Integrations

The Docker architecture makes the tool agnostic to your programming language.

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
| **License** | FSL 1.1 (Free for non-competing use) | Commercial (SLA & Indemnity) |
| **Extraction** | **Full Data** | **Full Data** |
| **Validation** | **Teaser Mode** (1 error) | **Official Engine** (SaxonC / Parity with Chorus Pro) |
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
