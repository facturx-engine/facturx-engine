# Factur-X Engine — EN16931 · ZUGFeRD 2.3 · Factur-X 1.0 · XRechnung 3.0 · PDF/A-3

> **The Privacy-First e-Invoicing API.** 100% Air-gapped. Saxon-HE Validation at Chorus Pro / KoSIT parity. Generate and Validate Factur-X 1.0, ZUGFeRD 2.x, XRechnung 3.0 — no cloud, no telemetry, no SaaS lock-in.

[![Docker Pulls](https://img.shields.io/docker/pulls/facturxengine/facturx-engine)](https://hub.docker.com/r/facturxengine/facturx-engine) [![GitHub](https://img.shields.io/badge/github-repo-181717?logo=github)](https://github.com/facturx-engine/facturx-engine) [![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://opensource.org/licenses/MIT) ![Air-Gapped](https://img.shields.io/badge/Privacy-Air_Gapped-success) ![Saxon-HE](https://img.shields.io/badge/Validation-Saxon--HE-blue)

---

## Why Factur-X Engine?

| Property | Detail |
|:---|:---|
| **Standards** | EN 16931, Factur-X 1.0, ZUGFeRD 2.3, XRechnung 3.0, Peppol BIS |
| **Validation Engine** | Saxon-HE — same Schematron as **Chorus Pro (France)** and **KoSIT (Germany)** |
| **Air-Gapped** | 100% offline. GDPR, DORA, CRA compliant. Zero outbound calls. |
| **Mandate Ready** | France (PPF/PDP 2026) · Germany (ZUGFeRD 2025) · EU ViDA (2027) |
| **Security** | SBOM (CycloneDX) included · Cosign-signed image · No telemetry |

---

## Quickstart

```bash
# Start the engine (Community Edition — free, MIT)
docker run -d -p 8000:8000 --name facturx-engine facturxengine/facturx-engine:latest
```

Or with Docker Compose:

```yaml
services:
  facturx:
    image: facturxengine/facturx-engine:latest
    ports:
      - "8000:8000"
    environment:
      - PORT=8000
      - WORKERS=4
      # - LICENSE_KEY=your_pro_key_here
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
      interval: 30s
      timeout: 10s
      retries: 3
```

---

## Core Workflows

### `/v1/validate` — Compliance Gate (EN 16931 Schematron, KoSIT / Chorus Pro parity)

Check any CII or UBL invoice (PDF or XML) against EN 16931 before sending to PDP/PPF.

```bash
curl -X POST "http://localhost:8000/v1/validate" \
  -F "file=@invoice.pdf"
```

### `/v1/xml` — Generate EN 16931 CII/UBL XML

Transform your ERP JSON metadata into a Cross-Industry Invoice XML.

```bash
curl -X POST "http://localhost:8000/v1/xml" \
  -H "Content-Type: application/json" \
  -d '{
    "invoice_number": "INV-2025-001",
    "issue_date": "20250901",
    "seller": { "name": "My Company", "vat_number": "FR12345678901" },
    "buyer": { "name": "Client GmbH" },
    "lines": [{ "name": "Consulting", "net_price": 1000.00, "vat_rate": 20.0 }],
    "amounts": { "grand_total": "1200.00" }
  }' -o invoice.xml
```

### `/v1/merge` — Embed XML into PDF (ZUGFeRD / Factur-X PDF/A-3b)

Embed an existing XML (Factur-X, ZUGFeRD, XRechnung) into a PDF/A-3b container.

```bash
curl -X POST "http://localhost:8000/v1/merge" \
  -F "pdf=@dolibarr_invoice.pdf" \
  -F "xml=@invoice.xml" \
  --output facturx_compliant.pdf
```

### `/v1/extract` — Extract Structured Data from ZUGFeRD / Factur-X PDF

Pull structured invoice data from a received Factur-X/ZUGFeRD PDF.

```bash
curl -X POST "http://localhost:8000/v1/extract" \
  -F "file=@received_invoice.pdf"
```

## Advanced Capabilities

### `/v1/convert` — One-Step PDF Generation

Convenience shortcut: generates XML from JSON metadata and embeds it into your PDF in a single call.

```bash
curl -X POST "http://localhost:8000/v1/convert" \
  -F "pdf=@examples/invoice_raw.pdf" \
  -F "metadata=$(cat examples/simple_invoice.json)" \
  --output invoice_compliant.pdf
```

### `/v1/serialize` — ERP-Ready JSON (Pro)

Returns a normalized, typed JSON object ready to import into any ERP or accounting system.

```bash
curl -X POST "http://localhost:8000/v1/serialize" \
  -F "file=@invoice.pdf"
```

---

## Community vs Pro

| Feature | Community (MIT) | Pro | OEM | Enterprise |
| :--- | :--- | :--- | :--- | :--- |
| **EN 16931 Validation** | ✅ | ✅ | ✅ | Custom Rules |
| **Smart Diagnostics** | ❌ | ✅ | ✅ | ✅ |
| **ERP-Ready JSON (`/v1/serialize`)** | ❌ | ✅ | ✅ | ✅ |
| **PDF/A-3b Compliance (VeraPDF)** | ❌ | ✅ | ✅ | ✅ |
| **Redistribution** | Internal Use | Internal | ✅ | ✅ |
| **Support** | Community | Priority | SLA | Dedicated |

**30-Day Free Pro Evaluation**: [facturx-engine.lemonsqueezy.com](https://facturx-engine.lemonsqueezy.com)

---

## Configuration

| Variable | Description | Default |
| :--- | :--- | :--- |
| `PORT` | API listening port | `8000` |
| `WORKERS` | Gunicorn worker count | `4` |
| `LICENSE_KEY` | Pro/OEM license key | — |
| `METRICS_ENABLED` | Enable Prometheus `/metrics` | `false` |
| `CORS_ORIGINS` | Allowed CORS origins (comma-sep) | `*` |

---

## Documentation & Demo

- 📖 **[Full API Reference](https://facturx-engine.github.io/facturx-engine/ref/api-reference.html)**
- 🤗 **[Interactive Demo (HuggingFace)](https://huggingface.co/spaces/Facturx-engine/factur-x-engine-demo)** — test with your own files
- 🐍 **[Python SDK](https://pypi.org/project/facturx-engine/)** (`pip install facturx-engine`)
- 🔗 **[GitHub Source](https://github.com/facturx-engine/facturx-engine)**

---

## Legal

**Vendor**: Factur-X Engine (Paris, France) | **License**: MIT / Commercial
**Compliance**: EU Cyber Resilience Act (CRA) Ready | **Security**: SBOM (CycloneDX) included · Cosign-signed

> This software is a technical tool. Users retain full responsibility for fiscal accuracy.

---

*Maintained by the Factur-X Engine Team.*
<!-- CI Verified -->
