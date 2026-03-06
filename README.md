# Factur-X Engine

> **The Privacy-First Invoicing Engine.** 100% Air-gapped, Official Saxon-HE Validation (Chorus Pro / KoSIT Parity). Generate and Validate Factur-X, ZUGFeRD 2.x, and XRechnung without cloud dependencies.

![Docker Pulls](https://img.shields.io/docker/pulls/facturxengine/facturx-engine) [![Hugging Face Spaces](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Live%20Demo-blue)](https://huggingface.co/spaces/Facturx-engine/factur-x-engine-demo) [![GitHub](https://img.shields.io/badge/github-repo-181717?logo=github)](https://github.com/facturx-engine/facturx-engine) [![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://opensource.org/licenses/MIT) ![Standard](https://img.shields.io/badge/standard-EN16931-green.svg) ![Privacy First](https://img.shields.io/badge/Privacy-Air_Gapped-success?logo=shield-dog) ![Saxon-HE](https://img.shields.io/badge/Powered_By-Saxon--HE-blue)

---

## Why Factur-X Engine?

- **Air-Gapped by Design**: 100% offline execution. No outbound network calls. GDPR/DORA compliant.
- **Official Saxon-HE Validation**: Technical parity with **Chorus Pro (France)** and **KoSIT (Germany)** portals — including EN16931 + BR-FR CTC v1.2.0 rules (FNFE/DGFIP) for French invoices.
- **Smart Diagnostics Engine (Pro)**: Proactively detects "Angles Morts" (e.g. invalid IBANs, >2 decimals, bizarre dates) that technically pass standard validation but fail on governmental platforms.
- **Mandate Ready**: Compliant with **France 2026 (PDP/PPF)** and **Germany 2025** electronic invoicing requirements.

### Architecture Decisions (Zero Memory Leaks)

- **Isolated Java Subprocesses**: Unlike traditional Python/Java wrappers that suffer from fatal JVM memory leaks under load, Factur-X Engine executes Schematron (Saxon-HE) and PDF/A-3 (VeraPDF) validations as isolated, sandboxed subprocesses. Memory is instantly reclaimed by the OS, guaranteeing enterprise-grade stability.
- **Air-Gap First**: To guarantee stability in secure environments (Banking, Defense), we do not use auto-updates or cloud "phone-homing". Licensing is verified via offline cryptographic signatures (Ed25519).

---

## Quickstart

```bash
docker run -d -p 8000:8000 --name facturx-engine facturxengine/facturx-engine:latest
```

### Core Workflows

#### 1. Validate — Compliance Gate

Check any CII or UBL invoice (PDF or XML) against EN 16931 before sending to PDP/PPF.

```bash
curl -X POST "http://localhost:8000/v1/validate" \
  -F "file=@invoice.xml"
```

#### 2. Generate XML — Business Data to CII/UBL

Transform your ERP JSON metadata into a Cross-Industry Invoice XML.

```bash
curl -X POST "http://localhost:8000/v1/xml" \
  -F "metadata=$(cat examples/simple_invoice.json)" \
  -o invoice.xml
```

#### 3. Merge — Assemble PDF + XML

Embed an existing XML (Factur-X, ZUGFeRD, XRechnung) into a PDF/A-3b container.

```bash
curl -X POST "http://localhost:8000/v1/merge" \
  -F "pdf=@examples/invoice_raw.pdf" \
  -F "xml=@invoice.xml" \
  --output invoice_compliant.pdf
```

#### 4. Extract — Receive Supplier Invoices

Pull structured invoice data from a received Factur-X/ZUGFeRD PDF.

```bash
curl -X POST "http://localhost:8000/v1/extract" \
  -F "file=@invoice.pdf"
```

### Advanced Capabilities

#### `/v1/convert` — One-Step PDF Generation

Convenience shortcut that generates XML from JSON metadata and embeds it into your PDF in a single call.

```bash
curl -X POST "http://localhost:8000/v1/convert" \
  -F "pdf=@examples/invoice_raw.pdf" \
  -F "metadata=$(cat examples/simple_invoice.json)" \
  --output invoice_compliant.pdf
```

#### `/v1/serialize` — ERP-Ready JSON (Pro)

Returns a normalized, typed JSON object ready to import directly into any ERP or accounting system. See [details below](#v1serialize--erp-ready-json-pro-1).

```bash
curl -X POST "http://localhost:8000/v1/serialize" \
  -F "file=@invoice.pdf"
```

**Windows users:** Replace `curl` with `curl.exe` and use PowerShell syntax for file reading.

---

## Documentation

**[Full API Reference](https://facturx-engine.github.io/facturx-engine/ref/api-reference.html)** - All endpoints, parameters, and response formats  
**[Integration Recipes](https://facturx-engine.github.io/facturx-engine/#api)** - Python, Node.js, PHP integration guides  
**[FAQ & Troubleshooting](https://facturx-engine.github.io/facturx-engine/guides/error-codes.html)** - Common issues and error codes  
**[OpenAPI Specification](https://raw.githubusercontent.com/facturx-engine/facturx-engine/main/docs/openapi.json)** - Machine-readable API spec
**[Changelog](https://github.com/facturx-engine/facturx-engine/releases)** - Version history and release notes

---

## Community vs Pro

This **Community** version is production-ready. The code is Open Core (transparent Python).

| Feature | Community Edition | Pro Edition | OEM Edition | Enterprise |
| :--- | :--- | :--- | :--- | :--- |
| **Pricing** | **Free** (MIT) | **990€ / year** | **2490€ / year** | **Contact Us** |
| **Usage** | Internal Use | Internal Use | **Redistribution** | High Volume |
| **Data Format** | Raw Extraction | **ERP-Ready JSON** | **ERP-Ready JSON** | Custom |
| **XML Validation** | Structural & Business Rules (Raw) | **Smart Diagnostics** (Pre-Clearance Audit) | **Smart Diagnostics** (Pre-Clearance Audit) | Custom Rules |
| **PDF Compliance** | ❌ | **VeraPDF (PDF/A-3)** | **VeraPDF (PDF/A-3)** | **VeraPDF (PDF/A-3)** |
| **Support** | Community | **Priority** | **SLA** | Dedicated |

### `/v1/serialize` — ERP-Ready JSON (Pro)

Unlike raw XML extraction, `/v1/serialize` returns a normalized, typed JSON object ready to import directly into any ERP or accounting system:

```json
{
  "success": true,
  "invoice": {
    "invoice_number": "INV-2025-0042",
    "invoice_date": "2025-03-01",
    "due_date": "2025-03-31",
    "currency": "EUR",
    "seller": { "name": "ACME SAS", "vat_number": "FR12345678901", "siret": "12345678900012" },
    "buyer": { "name": "Client Corp", "buyer_reference": "PO-9981" },
    "line_items": [
      { "name": "Consulting services", "quantity": 5, "unit_code": "HUR", "net_price": 150.00, "line_total": 750.00, "vat_rate": 20.0 }
    ],
    "tax_breakdown": [{ "category": "S", "rate": 20.0, "basis_amount": 750.00, "tax_amount": 150.00 }],
    "total_net_amount": 750.00,
    "total_tax_amount": 150.00,
    "total_gross_amount": 900.00,
    "amount_due": 900.00,
    "format": "factur-x",
    "profile": "en16931"
  }
}
```

### `/v1/validate` — Smart Diagnostics Engine (Pro)

While the Community edition runs standard EN 16931 Schematron validation, the **Pro Edition** features a Smart Diagnostics engine that translates crypting XPath errors into human-readable actions, and runs a **Proactive Scan** for silent platform killers:

- `INVALID-IBAN`: Catches malformed IBAN sequences.
- `TOO-MANY-DECIMALS`: Rejects amounts with `>2` fractional digits (e.g. `100.005`) that cause arithmetic truncation errors on Chorus Pro.
- `INVALID-DATE`: Flags dates from the distant past or future.
- `TYPE-AMOUNT-MISMATCH`: Detects negative invoice totals masquerading as standard invoices (instead of credit notes).

### 30-Day Evaluation (Product-Led Growth)

Test **100% of the Pro features (VeraPDF, Smart Diagnostics, and ERP Serialization)** on your own files, within your own infrastructure, during a 30-Day Evaluation period.

1. Request your evaluation key at **[Factur-X Engine on Lemon Squeezy](https://facturx-engine.lemonsqueezy.com)** (Zero friction, instant delivery).
2. VeraPDF and Saxon-HE are **already bundled** inside the Docker image. Just inject your key:

   ```bash
   docker run -d -p 8000:8000 \
     -e LICENSE_KEY='YOUR_KEY' \
     facturxengine/facturx-engine:latest
   ```

3. After 30 days, the engine smoothly transitions back to the Community Edition. No aggressive locks, your internal validation flows continue to operate.

### Configuration (Environment Variables)

The API behaves according to standard Linux paradigms. It accepts the following variables:

| Variable | Default | Description |
| :--- | :--- | :--- |
| `LICENSE_KEY` | *(empty)* | Activates Pro Features. Leave empty for Community Edition. |
| `MAX_UPLOAD_SIZE_MB` | `10` | Defence-in-depth size limit for payload processing. |
| `FX_VALIDATION_TIMEOUT` | `30` | Timeout in seconds for subprocess validators (Saxon/VeraPDF). |
| `VERAPDF_ENABLED` | `true` | System-wide toggle for PDF/A-3b validation (**Pro only**, requires `VERAPDF_JAR`). Has no effect in Community Edition. |
| `VERAPDF_JAR` | *(empty)* | **REQUIRED FOR PRO**: Absolute path to the VeraPDF Greenfield JAR. |
| `SAXON_JAR` | *(empty)* | Absolute path to the Saxon-HE JAR for Schematron evaluation. |
| `METRICS_ENABLED` | `false` | Enables the `/metrics` endpoint in Pro Mode. |
| `METRICS_TOKEN` | *(empty)* | Bearer token required for `/metrics` access in Pro Mode. |
| `CORS_ORIGINS` | *(empty)* | Comma-separated list of allowed origins (e.g., `http://localhost:3000,https://app.example.com`). |
| `WORKERS` | `4` | Number of Gunicorn worker processes (adjust based on CPU cores). |

---

## Operations & Monitoring

The container exposes endpoints designed for DevOps and infrastructure teams:

| Endpoint | Purpose | Availability |
| :--- | :--- | :--- |
| `GET /health` | Liveness probe (Kubernetes). Returns 200 OK immediately — no subprocess overhead. | All Editions |
| `GET /healthz` | Readiness probe. Checks JRE, VeraPDF, and Saxon-HE availability. Returns 503 if degraded. | All Editions |
| `GET /diagnostics` | Full system dump (versions, memory, config). | All Editions |
| `GET /metrics` | Prometheus metrics scrape target. | Pro Edition Only |

### Security Hardening (Prometheus Metrics)

The `/metrics` endpoint requires explicit activation and authentication to prevent business intelligence leakage.

1. **Activation**: Must set `METRICS_ENABLED=true`
2. **Authentication**: Must define `METRICS_TOKEN=your_secure_random_string`
3. **Scraping**: Configure Prometheus to pass the Authorization header: `Authorization: Bearer your_secure_random_string`

### Recommended Reverse-Proxy Configuration

Even with token authentication, it is an industry best practice to restrict access to the `/metrics` endpoint to your internal monitoring infrastructure (e.g., `127.0.0.1` or a specific VPC subnet).

**Nginx Example:**

```nginx
location /metrics {
    allow 127.0.0.1;
    allow 10.0.0.0/8;
    deny all;
    proxy_pass http://facturx-engine:8000;
}
```

---

## Legal & Compliance

**Vendor**: NexaFlow
**License**: [MIT](https://opensource.org/licenses/MIT) (Community) / Commercial (Pro)
**Compliance**: Designed to respect the EU **Cyber Resilience Act (CRA)**

> **IMPORTANT**: This software is a technical tool for data formatting. It does not replace professional tax advice. Users retain full responsibility for fiscal accuracy. See [full legal disclaimer](https://facturx-engine.github.io/facturx-engine/).

---

*Maintained by the Factur-X Engine Team.*
