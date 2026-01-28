# Factur-X Engine v1.3 "Security & Compliance Edition"

> **Factur-X Engine** is a stateless, air-gapped Docker container providing a REST API to **Generate**, **Validate**, and **Extract** electronic invoices. It ensures 100% compliance with **EN 16931**, **ZUGFeRD 2.4**, and **XRechnung 3.0** standards without requiring external dependencies or internet access.

![Docker Pulls](https://img.shields.io/docker/pulls/facturxengine/facturx-engine) [![GitHub](https://img.shields.io/badge/github-repo-181717?logo=github)](https://github.com/facturx-engine/facturx-engine) ![License](https://img.shields.io/badge/license-Community-blue.svg) ![Standard](https://img.shields.io/badge/standard-EN16931-green.svg) [![CRA](https://img.shields.io/badge/EU_CRA-Ready-blueviolet)](docs/cra.md)

---

## Quickstart

Runs immediately on any Docker host. No Python/Java dependencies.

```bash
# 1. Start the Engine (API)
docker run -d -p 8000:8000 --name facturx-engine facturxengine/facturx-engine:latest

# 2. Download example files (from GitHub)
curl -O https://raw.githubusercontent.com/facturx-engine/facturx-engine/main/examples/invoice_raw.pdf
curl -O https://raw.githubusercontent.com/facturx-engine/facturx-engine/main/examples/simple_invoice.json

# 3. Generate compliant invoice (Merge PDF + Data)
curl -X POST "http://localhost:8000/v1/convert" \
  -F "pdf=@invoice_raw.pdf" \
  -F "metadata=$(cat simple_invoice.json)" \
  --output invoice_compliant.pdf
```

### Extract to JSON (Open Core)

The Community Edition extracts **full financial and identity data**. No masking, no obfuscation.

```bash
curl -X POST "http://localhost:8000/v1/extract" \
  -F "pdf=@invoice_compliant.pdf"
```

**Response Preview:**

```json
{
  "invoice_id": "INV-2024-001",
  "issue_date": "2024-10-05",
  "seller": { "name": "Acme Corp" },
  "totals": { "net_amount": "1500.00", "tax_amount": "300.00" }
}
```

### Validation (Teaser vs Pro)

The engine validates files against the official **EN 16931 Schematron** rules using the SaxonC-HE engine.

* **Community Mode (No Key)**: Returns the **first** compliance error found and a count of remaining hidden errors (Teaser Mode).
* **Pro Mode (License Key)**: Returns the **full** list of all validation errors/warnings suitable for compliance reporting.

```bash
curl -X POST "http://localhost:8000/v1/validate" -F "pdf=@invoice_compliant.pdf"
```

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
| **License** | Open Source (MIT) | Commercial |
| **Extraction** | **Full Data** | **Full Data** |
| **Validation** | **Teaser Mode** (1 error) | **Full Report** (SaxonC) |
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

## Legal & Compliance

* **Vendor**: Factur-X Engine (Paris, France).
* **Compliance**: Designed to respect the EU **Cyber Resilience Act (CRA)**.
* **Security**: Image scanned (Trivy), SBOM (CycloneDX) included.

---

## FAQ

### Q: Does it require an internet connection?

**A:** No. The container is strictly **air-gapped** by design. It contains all necessary schemas (XSD) and Schematron rules (XSLT) internally.

### Q: Why use a Docker container instead of a library?

**A:** PDF/A-3 conversion requires complex system dependencies. Using a Docker container isolates this complexity, ensuring an **"Iso-Prod"** environment everywhere.

---

*Maintained by the Factur-X Engine Team.*
