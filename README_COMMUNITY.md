# 🚀 Factur-X API (Community Edition)

<div align="center">
  
  **The Developer-First Engine for Electronic Invoicing (EN 16931 / ZUGFeRD 2.2)**
  
  [![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)
  [![Status](https://img.shields.io/badge/status-production--ready-green.svg)]()
  
  [Quickstart](#quickstart) • [Documentation](#documentation) • [🔥 Upgrade to Pro](#-upgrade-to-pro)
</div>

---

## What is this?

**Factur-X API** is a stateless Docker "appliance" to handle the complex Factur-X / ZUGFeRD e-invoicing standard.

The **Community Edition** (this repo) allows you to:

* ✅ **Convert** PDF + JSON to Factur-X (PDF/A-3)
* ✅ **Validate** compliance against EN 16931 rules
* ✅ **Self-Host** with Docker (unlimited usage)

Need to **Extract data (JSON)** from invoices or get **Compliance Diagnostics**? Check out the [Pro Edition](#-upgrade-to-pro).

---

## ⚡ Quickstart

### 1. Run with Docker

```bash
docker run -d -p 8000:8000 --name facturx-api facturx-api:community
```

### 2. Convert a PDF

```bash
curl -X POST "http://localhost:8000/v1/convert" \
  -F "pdf=@invoice.pdf" \
  -F "metadata=@data.json" \
  -o factur-x.pdf
```

### 3. Validate Compliance

```bash
curl -X POST "http://localhost:8000/v1/validate" \
  -F "file=@factur-x.pdf"
```

👉 **Interactive Docs:** Open `http://localhost:8000/docs`

---

## 🔥 Upgrade to Pro (Universal Adapter)

The **Factur-X Engine Pro** is the production-grade "Universal Adapter" for e-invoicing.

| Feature | Community (Free) | Pro License |
| :--- | :---: | :---: |
| **Convert & Validate** | ✅ | ✅ |
| **Extract Normalization** | ❌ | ✅ (**Unified JSON Schema**) |
| **Trust Pack (CRA + SBOM)** | ❌ | ✅ (**Security Audit Ready**) |
| **Diagnostics & Metrics** | ❌ | ✅ |
| **Commercial License** | ❌ | ✅ (SaaS / OEM allowed) |
| **Support SLA** | None | None (Self-Hosted) |
| **Price** | Free | **499€ / year** (Standard) | **1 999€ / year** (OEM) |
| **Updates** | N/A | Included while active | Included while active |
| **Fallback** | N/A | Perpetual Use of last version | Perpetual Use of last version |

### Why Upgrade?

1. **The "Universal Adapter"**: Our `/v1/extract` endpoint ingests ANY compliant Factur-X/ZUGFeRD profile (Minimum, Basic, EN16931, XRechnung) and outputs a **single, normalized JSON format**. Stop handling XML namespaces and XSD versions yourself.
2. **Production Ready**: Includes system health checks, memory monitoring, and support bundle generation for your ops team.
3. **Legal Peace of Mind**: Comes with a Commercial License allowing integration into your proprietary products.

[👉 **Get the Pro Edition (Docker Image)**](https://facturx-engine.com/buy)
*(Secure Docker Image delivery + EULA)*

---

## 🛠️ Build from Source

```bash
# Clone this repo
git clone https://github.com/yourusername/facturx-api.git

# Build
docker build -t facturx-api:community .

# Run
docker run -p 8000:8000 facturx-api:community
```

---

## License

This Community Edition is open-sourced under the MIT License.
