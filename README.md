# Factur-X Engine

> **The self-hosted translation layer between your ERP and e-invoicing.** Ingest, validate, and normalize Factur-X, UBL, and CII into usable JSON - or generate compliant XML from your business data.

![Docker Pulls](https://img.shields.io/docker/pulls/facturxengine/facturx-engine) [![Hugging Face Spaces](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Live%20Demo-blue)](https://huggingface.co/spaces/Facturx-engine/factur-x-engine-demo) [![GitHub](https://img.shields.io/badge/github-repo-181717?logo=github)](https://github.com/facturx-engine/facturx-engine) [![License](https://img.shields.io/badge/license-MIT-blue.svg)](https://opensource.org/licenses/MIT) ![Standard](https://img.shields.io/badge/standard-EN16931-green.svg) ![Privacy First](https://img.shields.io/badge/Privacy-Air_Gapped-success?logo=shield-dog) ![Saxon-HE](https://img.shields.io/badge/Powered_By-Saxon--HE-blue)

---

## Who It's For

Backend developers building **ERP, accounting, or SaaS** integrations who need to process EN 16931 e-invoices (Factur-X, ZUGFeRD, XRechnung) without maintaining their own XML parsing and validation stack.

---

## Quickstart

```bash
docker run -d -p 8000:8000 --name facturx-engine facturxengine/facturx-engine:latest
```

---

## Receive - Ingest Supplier Invoices

Your ERP receives a raw XML or PDF from a supplier. The engine validates it, extracts the data, and gives you clean JSON.

### 1. Validate - Compliance Gate

Check any CII or UBL invoice (PDF or XML) against EN 16931 Schematron rules before ingesting into your database.

```bash
curl -X POST "http://localhost:8000/v1/validate" \
  -F "file=@invoice.xml"
```

The response includes `validation_completeness` (`full` or `partial`) and `layers_executed` so your application knows exactly which checks ran.

### 2. Extract - Heuristic Best-Effort JSON

Pull structured data from a received Factur-X/ZUGFeRD PDF or standalone XML.

```bash
curl -X POST "http://localhost:8000/v1/extract" \
  -F "file=@invoice.pdf"
```

### 3. Serialize - ERP-Ready JSON (Pro)

Unlike raw extraction, `/v1/serialize` returns normalized ERP integration JSON with a [versioned schema](docs/schemas/serialize-response.v1.schema.json) and explicit `fallbacks_applied` transparency.

```bash
curl -X POST "http://localhost:8000/v1/serialize" \
  -F "file=@invoice.pdf"
```

```json
{
  "success": true,
  "schema_version": "1.0.0",
  "engine_version": "1.x.x",
  "invoice": {
    "invoice_number": "INV-2025-0042",
    "invoice_date": "2025-03-01",
    "due_date": "2025-03-31",
    "currency": "EUR",
    "seller": { "name": "ACME SAS", "vat_number": "FR12345678901" },
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

---

## Send - Generate Compliant Invoices

Your ERP has business data. The engine transforms it into regulation-compliant XML or PDF.

### 4. Generate XML - Business Data to CII

Transform your ERP JSON metadata into a Cross-Industry Invoice XML.

```bash
curl -X POST "http://localhost:8000/v1/xml" \
  -F "metadata=$(cat examples/simple_invoice.json)" \
  -o invoice.xml
```

### 5. Convert - One-Step PDF Generation

Generates XML from JSON metadata and embeds it into your PDF in a single call.

```bash
curl -X POST "http://localhost:8000/v1/convert" \
  -F "pdf=@examples/invoice_raw.pdf" \
  -F "metadata=$(cat examples/simple_invoice.json)" \
  --output invoice_facturx.pdf
```

### 6. Merge - Assemble PDF + XML

Embed an existing XML (Factur-X, ZUGFeRD, XRechnung) into a PDF container. Use `/v1/validate` on the output when PDF/A evidence is required.

```bash
curl -X POST "http://localhost:8000/v1/merge" \
  -F "pdf=@examples/invoice_raw.pdf" \
  -F "xml=@invoice.xml" \
  --output invoice_facturx.pdf
```

**Windows users:** Replace `curl` with `curl.exe` and use PowerShell syntax for file reading.

---

## Why Not Roll Your Own?

You can parse CII XML in a day. But EN 16931 compliance isn't parsing - it's **ongoing maintenance**:

- **Regulatory watch**: Schematron rules change with every spec revision (XRechnung 3.0.2, Factur-X 1.0.07...). Who updates your validation logic when Chorus Pro or KoSIT ships new business rules?
- **Edge-case coverage**: Real-world invoices contain malformed IBANs, amounts with 3+ decimal places that cause silent rounding errors, dates in the past, negative totals masquerading as standard invoices. The engine's test corpus covers 200+ of these cases.
- **Validation depth**: A syntactically valid invoice can still break your accounting pipeline. The engine runs the same Schematron rules as Chorus Pro and KoSIT, catching issues before they corrupt your database.

The engine absorbs that maintenance so your team doesn't have to.

---

## Documentation

**[Full API Reference](https://facturx-engine.github.io/facturx-engine/ref/api-reference.html)** - All endpoints, parameters, and response formats
**[Integration Recipes](https://facturx-engine.github.io/facturx-engine/#api)** - Python, Node.js, PHP integration guides
**[JSON Schema (v1)](docs/schemas/serialize-response.v1.schema.json)** - Versioned response contract for `/v1/serialize`
**[OpenAPI Specification](https://raw.githubusercontent.com/facturx-engine/facturx-engine/main/docs/openapi.json)** - Machine-readable API spec
**[Changelog](https://github.com/facturx-engine/facturx-engine/releases)** - Version history and release notes

---

## Community vs Pro

This **Community** edition is production-ready. Open Core (transparent Python, MIT license).

| | Community | Pro |
| :--- | :--- | :--- |
| **Receive** | `/v1/extract` - heuristic best-effort extraction JSON | `/v1/serialize` - normalized ERP integration JSON with [versioned schema](docs/schemas/serialize-response.v1.schema.json) + fallback transparency |
| **Validate** | EN 16931 Schematron (raw XPath errors) | **Smart Diagnostics** - human-readable errors + proactive scan |
| **PDF/A-3** | - | VeraPDF compliance check |
| **Support** | GitHub Issues | Priority email |

**Pricing & license options** (Pro, OEM, Enterprise): **[facturx-engine.lemonsqueezy.com](https://facturx-engine.lemonsqueezy.com)**

### Smart Diagnostics Engine (Pro)

The Pro edition translates cryptic XPath errors into human-readable actions, and runs a proactive scan for silent platform killers:

- `INVALID-IBAN`: Catches malformed IBAN sequences.
- `TOO-MANY-DECIMALS`: Rejects amounts with >2 fractional digits that cause truncation errors on Chorus Pro.
- `INVALID-DATE`: Flags dates from the distant past or future.
- `TYPE-AMOUNT-MISMATCH`: Detects negative totals masquerading as standard invoices.

### 30-Day Evaluation

Test 100% of the Pro features on your own files, within your own infrastructure.

1. Request your evaluation key at **[Factur-X Engine on Lemon Squeezy](https://facturx-engine.lemonsqueezy.com)** (instant delivery).
2. VeraPDF and Saxon-HE are **already bundled** inside the Docker image. Just inject your key:

   ```bash
   docker run -d -p 8000:8000 \
     -e LICENSE_KEY='YOUR_KEY' \
     facturxengine/facturx-engine:latest
   ```

3. After 30 days, the engine transitions back to Community Edition. No aggressive locks.

---

## Deployment

### Air-Gapped by Design

100% offline execution. No outbound network calls. GDPR/DORA compliant. Licensing is verified via offline cryptographic signatures (Ed25519).

### Architecture

Schematron (Saxon-HE) and PDF/A-3 (VeraPDF) validations run as isolated Java subprocesses. Memory is instantly reclaimed by the OS - no JVM memory leaks under load.

### Configuration

| Variable | Default | Description |
| :--- | :--- | :--- |
| `LICENSE_KEY` | *(empty)* | Activates Pro features. Leave empty for Community Edition. |
| `MAX_UPLOAD_SIZE_MB` | `10` | Size limit for uploaded files. |
| `FX_VALIDATION_TIMEOUT` | `30` | Timeout in seconds for Saxon/VeraPDF subprocesses. |
| `VERAPDF_ENABLED` | `true` | Toggle PDF/A-3b validation (Pro only). |
| `SAXON_JAR` | *(empty)* | Path to the Saxon-HE JAR for Schematron evaluation. |
| `CORS_ORIGINS` | *(empty)* | Allowed origins (e.g., `http://localhost:3000`). |
| `WORKERS` | `4` | Number of Gunicorn worker processes. |

### Operations & Monitoring

| Endpoint | Purpose | Availability |
| :--- | :--- | :--- |
| `GET /health` | Liveness probe (Kubernetes). | All Editions |
| `GET /healthz` | Readiness probe. Checks JRE, VeraPDF, Saxon-HE availability. | All Editions |
| `GET /diagnostics` | System dump (versions, memory, config). | All Editions |
| `GET /metrics` | Prometheus scrape target (requires `METRICS_ENABLED=true` + `METRICS_TOKEN`). | Pro Only |

---

## Legal & Compliance

**Vendor**: NexaFlow
**License**: [MIT](https://opensource.org/licenses/MIT) (Community) / Commercial (Pro)
**Compliance**: Designed to respect the EU **Cyber Resilience Act (CRA)**

> **IMPORTANT**: This software is a technical tool for data formatting. It does not replace professional tax advice. Users retain full responsibility for fiscal accuracy. See [full legal disclaimer](https://facturx-engine.github.io/facturx-engine/).

---

*Maintained by the Factur-X Engine Team.*

