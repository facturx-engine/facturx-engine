# Factur-X Engine

> **The Privacy-First Invoicing Engine.** 100% Air-gapped, Official SaxonC Validation (Chorus Pro / KoSIT Parity). Generate and Validate Factur-X, ZUGFeRD 2.x, and XRechnung without cloud dependencies.

![Docker Pulls](https://img.shields.io/docker/pulls/facturxengine/facturx-engine) [![Hugging Face Spaces](https://img.shields.io/badge/%F0%9F%A4%97%20Hugging%20Face-Live%20Demo-blue)](https://huggingface.co/spaces/Facturx-engine/factur-x-engine-demo) [![GitHub](https://img.shields.io/badge/github-repo-181717?logo=github)](https://github.com/facturx-engine/facturx-engine) ![License](https://img.shields.io/badge/license-Community-blue.svg) ![Standard](https://img.shields.io/badge/standard-EN16931-green.svg) ![Privacy First](https://img.shields.io/badge/Privacy-Air_Gapped-success?logo=shield-dog) ![SaxonC](https://img.shields.io/badge/Powered_By-SaxonC_HE-blue)

---

## Why Factur-X Engine?

- **Air-Gapped by Design**: 100% offline execution. No outbound network calls. GDPR/DORA compliant.
- **Official SaxonC Validation**: Technical parity with **Chorus Pro (France)** and **KoSIT (Germany)** portals.
- **Mandate Ready**: Compliant with **France 2026 (PDP/PPF)** and **Germany 2025** electronic invoicing requirements.

### Architecture Decisions (Zero Memory Leaks)

- **Isolated Java Subprocesses**: Unlike traditional Python/Java wrappers that suffer from fatal JVM memory leaks under load, Factur-X Engine executes Schematron (Saxon-HE) and PDF/A-3 (VeraPDF) validations as isolated, sandboxed subprocesses. Memory is instantly reclaimed by the OS, guaranteeing enterprise-grade stability.
- **Air-Gap First**: To guarantee stability in secure environments (Banking, Defense), we do not use auto-updates or cloud "phone-homing". Licensing is verified via offline cryptographic signatures (Ed25519).

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

# Validate compliance (skip PDF/A-3b verification for speed using validate_pdfa=false)
# curl -X POST "http://localhost:8000/v1/validate?validate_pdfa=false" \
#   -F "file=@invoice_compliant.pdf"

# Extract Data (Community)
# curl -X POST "http://localhost:8000/v1/extract" -F "file=@invoice.pdf"

# Serialize for ERP (Pro)
# curl -X POST "http://localhost:8000/v1/serialize" -F "file=@invoice.pdf"

# Generate XML only (without PDF)
# curl -X POST "http://localhost:8000/v1/xml" \
#   -H "Content-Type: application/json" \
#   -d @examples/simple_invoice.json

# Check System Diagnostics
# curl "http://localhost:8000/diagnostics"
```

**Windows users:** Replace `curl` with `curl.exe` and use PowerShell syntax for file reading.

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
| **Pricing** | **Free** (FSL 1.1) | **990€ / year** | **2490€ / year** | **Contact Us** |
| **Usage** | Internal Use | Internal Use | **Redistribution** | High Volume |
| **Data Format** | Raw Extraction | **ERP-Ready JSON** | **ERP-Ready JSON** | Custom |
| **XML Validation** | Structural & Business Rules (Raw) | **Smart Diagnostics** (Actionable Fixes) | **Smart Diagnostics** (Actionable Fixes) | Custom Rules |
| **PDF Compliance** | ❌ | **VeraPDF (PDF/A-3)** | **VeraPDF (PDF/A-3)** | **VeraPDF (PDF/A-3)** |
| **Support** | Community | **Priority** | **SLA** | Dedicated |

### 30-Day Evaluation (Product-Led Growth)

Test **100% of the Pro features (VeraPDF, Smart Diagnostics, and ERP Serialization)** on your own files, within your own infrastructure, during a 30-Day Evaluation period.

1. Request your evaluation key at **[Factur-X Engine on Lemon Squeezy](https://facturx-engine.lemonsqueezy.com)** (Zero friction, instant delivery).
2. Inject the Base64 key into your Docker container:
   `docker run -e LICENSE_KEY='YOUR_KEY' facturxengine/facturx-engine`
3. After 30 days, the engine smoothly transitions back to the Community Edition. No aggressive locks, your internal validation flows continue to operate.

### Configuration (Environment Variables)

The API behaves according to standard Linux paradigms. It accepts the following variables:

| Variable | Default | Description |
| :--- | :--- | :--- |
| `LICENSE_KEY` | *(empty)* | Activates Pro Features. Leave empty for Community Edition. |
| `MAX_UPLOAD_SIZE_MB` | `10` | Defence-in-depth size limit for payload processing. |
| `FX_VALIDATION_TIMEOUT` | `30` | Timeout in seconds for subprocess validators (Saxon/VeraPDF). |
| `VERAPDF_ENABLED` | `true` | System-wide toggle for PDF/A-3b validation (if `VERAPDF_JAR` is set). |
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
| `GET /health` | Liveness probe (Kubernetes). Returns 200 OK immediately if the HTTP server is up. | All Editions |
| `GET /healthz` | Readiness probe. Also checks internal dependencies (Java, Saxon). | All Editions |
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

## Roadmap

- **v2.0 (Planned)**: Full E-Reporting Support (Flux 10) and Lifecycle Management (Flux 11) for direct PDP integration.

---

## Legal & Compliance

**Vendor**: NexaFlow (SIREN: 999 899 834)  
**License**: FSL 1.1 (Community) / Commercial (Pro)  
**Compliance**: Designed to respect the EU **Cyber Resilience Act (CRA)**  

> **IMPORTANT**: This software is a technical tool for data formatting. It does not replace professional tax advice. Users retain full responsibility for fiscal accuracy. See [full legal disclaimer](https://facturx-engine.github.io/facturx-engine/).

---

*Maintained by the Factur-X Engine Team.*
