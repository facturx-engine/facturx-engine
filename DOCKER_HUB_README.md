# Factur-X Engine: Docker API for Factur-X, ZUGFeRD 2.2 & EN16931

> **Instantly transform PDFs and JSON data into compliant e-invoices. A self-hosted, lightweight, 100% Offline REST API based on Docker.**

[![Docker Pulls](https://img.shields.io/docker/pulls/facturxengine/facturx-engine)](https://hub.docker.com/r/facturxengine/facturx-engine)
[![License](https://img.shields.io/badge/license-Community-blue.svg)](https://github.com/facturx-engine/facturx-engine)
[![Standard](https://img.shields.io/badge/standard-EN16931-green.svg)](https://fnfe-mpe.org/factur-x/)
[![CRA](https://img.shields.io/badge/EU_CRA-Compliant-blueviolet?style=for-the-badge)](https://github.com/facturx-engine/facturx-engine/blob/main/_INTERNAL/docs/CRA_COMPLIANCE.md)

---

## ⚡ Quickstart

Generate your first Factur-X (PDF/A-3) invoice in less than 60 seconds. No Python or Java installation required.

```bash
# 1. Start the Engine (API)
docker run -d -p 8000:8000 --name facturx-engine facturxengine/facturx-engine:latest

# 2. Download example files (from GitHub)
curl -O https://raw.githubusercontent.com/facturxengine/facturx-engine/main/examples/invoice_raw.pdf
curl -O https://raw.githubusercontent.com/facturxengine/facturx-engine/main/examples/simple_invoice.json

# 3. Generate compliant invoice (Merge PDF + Data)
curl -X POST "http://localhost:8000/v1/convert" \
  -F "pdf=@invoice_raw.pdf" \
  -F "metadata=$(cat simple_invoice.json)" \
  --output invoice_compliant.pdf

echo "✅ Invoice generated: invoice_compliant.pdf"
```

👉 **[Swagger UI Documentation](http://localhost:8000/docs)** : <http://localhost:8000/docs>

---

## ✨ Key Features

Factur-X Engine solves **EN 16931** compliance complexity for developers.

* **Native PDF/A-3 Conversion**: Forget **Ghostscript** configuration hell and color profile issues. The engine handles ISO 19005-3 compliance automatically.
* **ZUGFeRD & Factur-X Validation**: Validate your XML files against official schemas (XSD + Schematron). Supports profiles: `MINIMUM`, `BASIC WL`, `BASIC`, `EN 16931`, `EXTENDED` (and `XRechnung` via mapping).
* **Stateless REST API**: Microservice architecture ideal for Kubernetes, Docker Swarm, or CI/CD pipelines. **Zero data persistence** (Privacy by Design).
* **100% Offline & Sovereign**: The container requires no internet connection. Your financial data never leaves your infrastructure.
* **Data Extraction**: Transform incoming Factur-X PDFs into structured JSON for your ERP (Odoo, SAP, Dolibarr).

---

## 🚀 Use Cases & Integrations

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

## 🛠 Configuration

The container is configurable via environment variables:

| Variable | Description | Default |
| :--- | :--- | :--- |
| `PORT` | API Listening Port | `8000` |
| `WORKERS` | Number of Gunicorn Workers | `1` |
| `LOG_LEVEL` | Log Level (info, debug) | `info` |

---

## 🤝 Community vs Pro

This **Community** version is feature-complete, unlimited, and production-ready. The **Pro** edition offers guarantees and services for businesses.

| Feature | Community Edition (This Repo) 🆓 | Pro / Enterprise Edition 💎 |
| :--- | :--- | :--- |
| **License** | Open Source (MIT) | Commercial / Proprietary |
| **Usage** | Unlimited (Self-hosted) | Unlimited + **Legal Warranty** |
| **Generation** | ✅ Unlimited | ✅ Unlimited |
| **Validation** | ✅ Unlimited | ✅ Unlimited |
| **Extraction** | ⚠️ **Demo Mode** (Data masked `***`) | ✅ **Full Data Access** |
| **Support** | Community (GitHub Interactions) | Priority Email / SLA |

### 💰 Pricing & Licenses

**1. For Internal Use (SME / Bank / Corporate)**

* **Standard License**: Unlimited usage for your own company.

**2. For OEM & Integrators (SaaS / ERP)**

* **OEM Growth**: Commercial Redistribution. Standard Liability Terms.
* **OEM Scale (Contact Only)**: Enterprise Redistribution. **Includes Legal Indemnification & Insurance**.

> **ℹ️ Perpetual Fallback**: You keep the version you bought forever. The subscription covers updates, security patches & warranty.

👉 **[View Pricing & Licenses](https://facturx-engine.lemonsqueezy.com)**

---

## ⚖️ Legal & Compliance

* **Vendor**: Factur-X Engine (Paris, France).
* **Compliance**: Designed to respect the EU **Cyber Resilience Act (CRA)**.
* **Security**: Image scanned (Trivy), SBOM available.

*Built with ❤️ in Paris.*
