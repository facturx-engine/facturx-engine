# Factur-X Engine

> **The Privacy-First Invoicing Engine.** 100% Air-gapped, Official SaxonC Validation (Chorus Pro / KoSIT Parity). Generate and Validate Factur-X, ZUGFeRD 2.x, and XRechnung 3.0 without cloud dependencies.

![Docker Pulls](https://img.shields.io/docker/pulls/facturxengine/facturx-engine) [![GitHub](https://img.shields.io/badge/github-repo-181717?logo=github)](https://github.com/facturx-engine/facturx-engine) ![License](https://img.shields.io/badge/license-Community-blue.svg) ![Standard](https://img.shields.io/badge/standard-EN16931-green.svg) ![Privacy First](https://img.shields.io/badge/Privacy-Air_Gapped-success?logo=shield-dog) ![SaxonC](https://img.shields.io/badge/Powered_By-SaxonC_HE-blue)

---

## Why Factur-X Engine?

- **Air-Gapped by Design**: 100% offline execution. No outbound network calls. GDPR/DORA compliant.
- **Official SaxonC Validation**: Technical parity with **Chorus Pro (France)** and **KoSIT (Germany)** portals.
- **Mandate Ready**: Compliant with **France 2026 (PDP/PPF)** and **Germany 2025** electronic invoicing requirements.

---

## Quickstart

```bash
# Start the engine
docker run -d -p 8000:8000 --name facturx-engine facturxengine/facturx-engine:latest

# Generate compliant Factur-X invoice
curl -X POST "http://localhost:8000/v1/convert" \
  -F "pdf=@examples/invoice_raw.pdf" \
  -F "metadata=$(cat examples/simple_invoice.json)" \
  --output invoice_compliant.pdf

# Validate compliance
curl -X POST "http://localhost:8000/v1/validate" \
  -F "file=@invoice_compliant.pdf"
```

**Windows users:** Replace `curl` with `curl.exe` and use PowerShell syntax for file reading.

---

## Documentation

**[Full API Reference](https://facturx-engine.github.io/facturx-engine/ref/api-reference.html)** - All endpoints, parameters, and response formats  
**[Integration Recipes](https://facturx-engine.github.io/facturx-engine/#api)** - Python, Node.js, PHP integration guides  
**[FAQ & Troubleshooting](https://facturx-engine.github.io/facturx-engine/guides/error-codes.html)** - Common issues and error codes  
**[OpenAPI Specification](https://raw.githubusercontent.com/facturx-engine/facturx-engine/main/docs/openapi.json)** - Machine-readable API spec

---

## Community vs Pro

This **Community** version is production-ready. The code is Open Core (transparent Python).

| Feature | Community Edition | Pro Edition | OEM Edition | Enterprise |
| :--- | :--- | :--- | :--- | :--- |
| **Pricing** | **Free** (FSL 1.1) | **490€ / year** | **2490€ / year** | **Contact Us** |
| **Usage** | Internal Use | Internal Use | **Redistribution** | High Volume |
| **Extraction** | Full Data | **Business JSON** | **Business JSON** | Custom |
| **Validation** | EN 16931 Rules | **Smart Diagnostics** | **Smart Diagnostics** | Custom Rules |
| **Support** | Community | **Priority** | **SLA** | Dedicated |

### Try Pro Features for Free

Upload one of our official reference files to unlock **all Pro features** without a license:

- **Smart Diagnostics**: Use files from `tests/corpus/invalid/` to see human-readable error explanations
- **Business-Ready Serialization**: Use files from `tests/corpus/valid/` to extract structured JSON

The engine recognizes these files via MD5 hash and automatically enables Trial Mode.

**[Get Pro License](https://facturx-engine.lemonsqueezy.com)**

---

## Configuration

| Variable | Description | Default |
| :--- | :--- | :--- |
| `PORT` | API Listening Port | `8000` |
| `LICENSE_KEY` | Pro License Key (Base64) | - |
| `WORKERS` | Number of Gunicorn Workers | `1` |

---

## Legal & Compliance

**Vendor**: Factur-X Engine (Paris, France)  
**License**: FSL 1.1 (Community) / Commercial (Pro)  
**Compliance**: Designed to respect the EU **Cyber Resilience Act (CRA)**  

> **IMPORTANT**: This software is a technical tool for data formatting. It does not replace professional tax advice. Users retain full responsibility for fiscal accuracy. See [full legal disclaimer](https://facturx-engine.github.io/facturx-engine/).

---

*Maintained by the Factur-X Engine Team.*
