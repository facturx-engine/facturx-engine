# Factur-X Engine Pro

Thank you for upgrading to **Factur-X Engine Pro**!
This guide will help you install, license, and use the engine in your production environment.

> [!IMPORTANT]
> Use of this software is subject to the [Commercial License (EULA)](EULA_PRO.md).
> Please also review our [CRA Compliance Statement](_INTERNAL/docs/CRA_COMPLIANCE.md).

---

## 1. Installation

You received the software as a Docker Archive (`.tar` file).

1. **Load the Image** into your Docker registry or local daemon:

    ```bash
    docker load -i facturx-pro-v1.3.1.tar
    ```

2. **Verify** successful import:

    ```bash
    docker images | grep facturx-pro
    # Should show: facturx-pro   v1.3.1
    ```

---

## 2. Activation & Running

You need your **LICENSE_KEY**.

Run the engine with the key as an environment variable:

```bash
docker run -d \
  -p 8000:8000 \
  -e LICENSE_KEY="YOUR_LICENSE_KEY_HERE" \
  --name facturx-pro \
  facturx-pro:v1.3.1
```

> **Note:** With a valid `LICENSE_KEY`, the engine unlocks Pro features (Full Validation Report, Business Metrics) and removes all usage limits.

---

## 3. API Usage

### Health Check

```bash
curl http://localhost:8000/health
# {"status": "healthy", "service": "factur-x-api", "version": "1.3.1"}
```

### Convert PDF to Factur-X

Turn a standard PDF into an electronic invoice (Factur-X/ZUGFeRD).

```bash
curl -X POST "http://localhost:8000/v1/convert" \
  -F "pdf=@invoice.pdf" \
  -F "metadata=@data.json" \
  -o factur-x.pdf
```

### Extract Data (Open Core)

Extract structured JSON data from **any** Factur-X/ZUGFeRD invoice (imported from suppliers).

```bash
curl -X POST "http://localhost:8000/v1/extract" \
  -F "file=@supplier_invoice.pdf"
```

### Validation (Pro Mode)

With your license key, the validation endpoint returns the **full compliance report** (instead of the Teaser).

```bash
curl -X POST "http://localhost:8000/v1/validate" -F "file=@invoice.pdf"
```

### Observability (Business Metrics)

Monitor your engine's performance in real-time. Because you have a valid license, you see **Business Metrics** in addition to Operational Metrics.

```bash
curl http://localhost:8000/metrics
```

**Metrics available:**

- `facturx_validation_outcome{mode="pro", result="invalid"}`
- `facturx_validation_profile{profile="en16931"}`
- `facturx_validation_error_type{rule_id="BR-CO-17"}`

---

## Support

For technical issues or updates:

- **Email:** <facturx.engine@protonmail.com>
- **Standards:** Fully compliant with **EN 16931**, **ZUGFeRD 2.2** and **Factur-X 1.0**.
- **Trust Pack:** Includes **CRA Compliance Statement** and **SBOM (CycloneDX)** for your security audits.
- **Updates:** You will receive email notifications for new versions (Security Patches).
- **Docs:** Full API documentation is available at `http://localhost:8000/docs` when running the container.

*Maintained by the Factur-X Engine Team.*
