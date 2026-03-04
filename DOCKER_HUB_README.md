# Factur-X Engine

> **The Privacy-First Invoicing Engine.** 100% Air-gapped, Official Saxon-HE Validation (Chorus Pro / KoSIT Parity). Generate and Validate Factur-X, ZUGFeRD 2.x, and XRechnung 3.0 without cloud dependencies.

[![Docker Pulls](https://img.shields.io/docker/pulls/facturxengine/facturx-engine)](https://hub.docker.com/r/facturxengine/facturx-engine) [![GitHub](https://img.shields.io/badge/github-repo-181717?logo=github)](https://github.com/facturx-engine/facturx-engine) [![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://opensource.org/licenses/MIT) ![Privacy First](https://img.shields.io/badge/Privacy-Air_Gapped-success?logo=shield-dog) ![Saxon-HE](https://img.shields.io/badge/Powered_By-Saxon--HE-blue)

---

## Why Factur-X Engine?

- **Air-Gapped by Design**: 100% offline execution. No outbound network calls. GDPR/DORA compliant.
- **Official Saxon-HE Validation**: Technical parity with **Chorus Pro (France)** and **KoSIT (Germany)** portals.
- **Mandate Ready**: Compliant with **France 2026 (PDP/PPF)** and **Germany 2025** electronic invoicing requirements.

---

## Quickstart

```bash
# Start the engine
docker run -d -p 8000:8000 --name facturx-engine facturxengine/facturx-engine:latest

# Generate compliant Factur-X XML
curl -X POST "http://localhost:8000/v1/xml" \
  -F "metadata=$(cat examples/simple_invoice.json)" \
  -o invoice.xml

# Merge XML into a PDF/A-3b container
curl -X POST "http://localhost:8000/v1/merge" \
  -F "pdf=@examples/invoice_raw.pdf" \
  -F "xml=@invoice.xml" \
  --output invoice_compliant.pdf
```

**[Full API Documentation](http://localhost:8000/docs)** (Swagger UI available after starting container)

---

## Documentation

**[API Reference](https://facturx-engine.github.io/facturx-engine/ref/api-reference.html)** - All endpoints & parameters  
**[Integration Guides](https://facturx-engine.github.io/facturx-engine/#api)** - Python, Node.js, PHP recipes  
**[Troubleshooting](https://facturx-engine.github.io/facturx-engine/guides/error-codes.html)** - Error codes & solutions

---

## Community vs Pro

| Feature | Community Edition | Pro Edition | OEM Edition | Enterprise |
| :--- | :--- | :--- | :--- | :--- |
| **Usage** | Internal Use | Internal Use | **Redistribution** | High Volume |
| **Data Format** | Raw Extraction | **ERP-Ready JSON** | **ERP-Ready JSON** | Custom |
| **XML Validation** | EN 16931 Rules | **Smart Diagnostics** | **Smart Diagnostics** | Custom Rules |
| **PDF Compliance** | ❌ | **VeraPDF (PDF/A-3)** | **VeraPDF (PDF/A-3)** | **VeraPDF (PDF/A-3)** |
| **Support** | Community | **Priority** | **SLA** | Dedicated |

### 30-Day Evaluation

Test **100% of the Pro features (VeraPDF, Smart Diagnostics, and ERP Serialization)** on your own files, within your own infrastructure, during a 30-Day Evaluation period.

1. Request your evaluation key at **[Factur-X Engine on Lemon Squeezy](https://facturx-engine.lemonsqueezy.com)** (Zero friction, instant delivery).
2. Inject the Base64 key into your Docker container:
   `docker run -e LICENSE_KEY='YOUR_KEY' facturxengine/facturx-engine`
3. After 30 days, the engine gracefully downgrades back to Community Mode. No forced lock-in.

---

## Configuration

| Variable | Description | Default |
| :--- | :--- | :--- |
| `PORT` | API Listening Port | `8000` |
| `LICENSE_KEY` | Pro License Key | - |
| `WORKERS` | Gunicorn Workers | `4` |

---

## Legal

**Vendor**: Factur-X Engine (Paris, France) | **License**: MIT / Commercial  
**Compliance**: EU Cyber Resilience Act (CRA) Ready | **Security**: SBOM included

> This software is a technical tool. Users retain full responsibility for fiscal accuracy. [Full legal disclaimer](https://github.com/facturx-engine/facturx-engine).

---

*Maintained by the Factur-X Engine Team.*
<!-- CI Verified -->
