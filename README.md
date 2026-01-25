# Factur-X Engine v1.3 "Security & Compliance Edition"

> **Factur-X Engine** is a stateless, air-gapped Docker container providing a REST API to **Generate**, **Validate**, and **Extract** electronic invoices. It ensures 100% compliance with **EN 16931**, **ZUGFeRD 2.4**, and **XRechnung 3.0** standards without requiring external dependencies or internet access.

![Docker Pulls](https://img.shields.io/docker/pulls/facturxengine/facturx-engine)
![License](https://img.shields.io/badge/license-Community-blue.svg)
![Standard](https://img.shields.io/badge/standard-EN16931-green.svg)
[![CRA](https://img.shields.io/badge/EU_CRA-Compliant-blueviolet?style=for-the-badge)](docs/cra.md)

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

echo "Invoice generated: invoice_compliant.pdf"
```

### Extract to JSON (Demo Mode)

```bash
curl -X POST "http://localhost:8000/v1/extract" \
  -F "pdf=@invoice_compliant.pdf"
```

**Interactive Documentation:** [http://localhost:8000/docs](http://localhost:8000/docs)

### Verification (Smoke Test)

You can verify your installation using the built-in smoke test script (Zero-Dependency):

```bash
docker exec -it facturx-engine python tools/smoke_test.py
```

This will check the Health API, PDF Conversion, EN 16931 Validation, and Data Extraction in one go.

---

## Technical Specifications

High-performance compliance engine for **EN 16931**.

* **Native PDF/A-3 Conversion**: Internal engine handles ISO 19005-3 conformance. **No external Ghostscript dependency**.
* **Standards Compliance**: Validates against **EN 16931**, **ZUGFeRD 2.2 / 2.4**, and **XRechnung 3.0**. Includes Native Schematron Rules (Business Logic) for France (SIRET, VAT) and Germany (Tax ID). No external Java dependencies.
* **Stateless Architecture**: Zero persistence. Input data is processed in-memory and discarded. Ideal for GDPR/Privacy.
* **Air-Gapped Ready**: 100% Offline execution. No outbound network requests required.
* **Structured Extraction**: Parses Factur-X XML into standard JSON for ERP integration.

---

## Comparison: Why Factur-X Engine?

| Feature | **Factur-X Engine** (Docker) | **Java Libraries** (Mustang) | **SaaS APIs** (Stripe/Generic) |
| :--- | :--- | :--- | :--- |
| **Architecture** | **Stateless Microservice** | Library (embedded) | External Service |
| **Privacy (GDPR)** | **100% On-Premise (Air-gapped)** | On-Premise | **Data sent to Cloud** |
| **Dependencies** | **Zero (Docker)** | Java JVM + Deps | None (HTTP) |
| **Validation** | **Native Schematron (EN 16931)** | Partial / Complex | Varies |
| **Performance** | **High (C++ PDF Engine)** | JVM Startup overhead | Network latency |

---

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
| `WORKERS` | Number of Gunicorn Workers | `1` |
| `LOG_LEVEL` | Log Level (info, debug) | `info` |

---

## Community vs Pro

This **Community** version is production-ready for generation/validation; extraction is demo-masked. The **Pro** edition offers guarantees and services for businesses.

| Feature | Community Edition (This Repo) | Pro / Enterprise Edition |
| :--- | :--- | :--- |
| **License** | Open Source (MIT) | Commercial / Proprietary |
| **Usage** | Unlimited (Self-hosted) | Unlimited + **Legal Warranty** |
| **Generation** | Included | Included |
| **Validation** | Included | Included |
| **Extraction** | **Demo Mode** (Data masked `***`) | **Full Data Access** |
| **Support** | Community (GitHub Discussions) | Priority Email / SLA |

### Pricing & Licenses

**1. For Internal Use (SME / Bank / Corporate)**

* **Standard License (499 € / year)**: Unlimited usage for your own company.

**2. For OEM & Integrators (SaaS / ERP)**

* **OEM Growth (2 490 € / year)**: Commercial Redistribution. Standard Liability Terms.
* **OEM Scale (Contact Us)**: Enterprise Redistribution. **Includes Legal Indemnification & Insurance**.

> **Perpetual Fallback**: You keep the version you bought forever. The subscription covers updates, security patches & warranty.

**[Get Pro License](https://facturx-engine.lemonsqueezy.com)**

---

## Legal & Compliance

* **Vendor**: Factur-X Engine (Paris, France).
* **Compliance**: Designed to respect the EU **Cyber Resilience Act (CRA)**.
* **Security**: Image scanned (Trivy), SBOM available.

## FAQ (Frequently Asked Questions)

### Q: Does it require an internet connection?

**A:** No. The container is strictly **air-gapped** by design. It contains all necessary schemas (XSD) and Schematron rules (XSLT) internally. It makes **zero** outbound network requests, making it safe for banks, defense, and high-security environments.

### Q: Why use a Docker container instead of a library?

**A:** PDF/A-3 conversion requires complex system dependencies (Ghostscript, fonts, color profiles). Using a Docker container isolates this complexity, ensuring an **"Iso-Prod"** environment everywhere (Dev, Staging, Prod) without "Works on my machine" issues.

### Q: Is it compliant with the French 2026 Reform (PDP)?

**A:** Yes. The engine produces files strictly compliant with the **EN 16931** syntax mandated by the French PPF (Portail Public de Facturation) and PDP candidates. It supports the "Minimum", "Basic WL", and "EN 16931" profiles.

---

*Maintained by the Factur-X Engine Team.*
