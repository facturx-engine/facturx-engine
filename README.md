# Factur-X Engine

Self-hosted Docker API for technical e-invoice workflows. It generates,
validates, inspects, and normalizes Factur-X/ZUGFeRD CII and XRechnung UBL
documents without uploading invoice data to a hosted service.

![Docker Pulls](https://img.shields.io/docker/pulls/facturxengine/facturx-engine)
[![GitHub](https://img.shields.io/badge/github-repo-181717?logo=github)](https://github.com/facturx-engine/facturx-engine)
[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

## Scope and responsibility

Factur-X Engine is a technical document-processing component. A successful API
call is not a tax, accounting, legal, or regulatory opinion. Your application
remains responsible for supplier matching, duplicate detection, purchase-order
matching, tax policy, payment approval, filing, and acceptance decisions.

Validation results only describe the rules and layers that actually ran. Check
`validation_completeness`, `layers_executed`, and `layers_skipped` before using
a result.

## Quickstart

```bash
docker run -d -p 8000:8000 --name facturx-engine \
  facturxengine/facturx-engine:latest
```

Open `http://localhost:8000/docs` for the runtime OpenAPI documentation.

## API workflows

### Receive invoices

| Endpoint | Contract |
| --- | --- |
| `POST /v1/validate` | Runs the validation layers available in the container and reports exactly which layers ran or were skipped. |
| `POST /v1/extract` | Best-effort preview of an embedded invoice. Always returns `mode: "preview"` and `suitable_for_automatic_import: false`. |
| `POST /v1/serialize` | Strict, versioned CII/UBL mapping. Refuses malformed XML, incomplete validation, invented defaults, silently skipped lines, and unsupported material groups. |

`/v1/extract` is useful for inspection and troubleshooting. It may expose
missing, coerced, or truncated values and must not be used as an automatic
accounting import decision.

`/v1/serialize` returns HTTP 200 only when validation is complete and the
document can be represented by schema version `2.0.0` without recovery or
fallback values. A successful response deliberately routes the caller to its
own remaining controls:

The contract is currently being tested as **Factur-X Engine Intake**. A free
[30-day evaluation key](https://facturx-engine.lemonsqueezy.com/checkout/buy/99a9ff62-baa6-4a24-ac61-3eebfacddab5)
enables it in the same public Docker image; without a key, the endpoint returns
`FEATURE_NOT_ENABLED`. There is no public **paid** checkout during the test.

The tested commercial hypothesis is **€299 excl. VAT, one-time, for one legal
entity and internal use**. Redistribution, OEM use, SLA, custom integration and
tax or accounting decisions are outside the proposed scope. This is a price
test, not an active offer for sale.

```json
{
  "success": true,
  "schema_version": "2.0.0",
  "execution_status": "complete",
  "mapping_status": "complete",
  "validation_status": "passed",
  "suggested_route": "continue_client_checks",
  "client_checks_required": [
    "supplier_master_match",
    "duplicate_invoice_check",
    "purchase_order_match",
    "tax_policy_check",
    "payment_approval"
  ]
}
```

Invalid, incomplete, or unsupported documents return HTTP 422 with stable
diagnostics containing `code`, `source`, `path`, and `message`.

### Send invoices

| Endpoint | Contract |
| --- | --- |
| `POST /v1/xml` | Generates CII XML from the documented metadata model. |
| `POST /v1/convert` | Generates CII XML and embeds it into a supplied PDF. Validate the result separately when PDF/A evidence is required. |
| `POST /v1/merge` | Embeds an existing supported XML document into a supplied PDF/A-3 container. |

The generation metadata model includes VAT exemption reason text, document and
line billing periods, purchase-order and preceding-invoice references, and an
optional VAT total in a distinct tax-accounting currency:

```json
{
  "tax_details": [{ "exemption_reason": "Reverse charge" }],
  "billing_period": { "start": "20260701", "end": "20260731" },
  "purchase_order_reference": "BC-1234",
  "preceding_invoices": [
    { "reference": "FA-2026-0042", "issue_date": "20260715" }
  ],
  "tax_accounting_currency_code": "GBP",
  "tax_accounting_currency_amount": "85.00"
}
```

The two tax-accounting currency fields must be provided together, and that
currency must differ from `currency_code`.

Example:

```bash
curl -X POST "http://localhost:8000/v1/validate" \
  -F "file=@invoice.xml"
```

```bash
curl -X POST "http://localhost:8000/v1/extract" \
  -F "file=@invoice.pdf"
```

```bash
curl -X POST "http://localhost:8000/v1/serialize" \
  -F "file=@invoice.xml"
```

```bash
curl -X POST "http://localhost:8000/v1/xml" \
  -F "metadata=$(cat examples/simple_invoice.json)" \
  -o invoice.xml
```

## Operations

| Endpoint | Purpose |
| --- | --- |
| `GET /health` | Lightweight liveness probe. |
| `GET /healthz` | Readiness and validation-tool availability, including an actual Saxon transform and temporary-file I/O probe. |
| `GET /diagnostics` | Protected runtime diagnostics. Configure `DIAGNOSTICS_TOKEN` outside development. |
| `GET /metrics` | Protected Prometheus output when explicitly enabled. |

The API is local by design, but deployment security remains the operator's
responsibility. Put it behind an authenticated reverse proxy or private network;
do not expose an unauthenticated container directly to the internet.

## Documentation

- [API reference](https://facturx-engine.github.io/facturx-engine/ref/api-reference.html)
- [OpenAPI specification](docs/openapi.json)
- [Strict serialization schema](docs/schemas/serialize-response.v2.schema.json)
- [Security policy](SECURITY.md)
- [Changelog](CHANGELOG.md)

## Licensing and commercial status

All code published in this repository is licensed under the [MIT License](LICENSE).
Intake is being tested in the same repository and Docker image through 30-day
evaluation keys. The key controls packaged feature availability; it does not
change the MIT rights granted over published source code.

There is currently no public paid checkout, SLA, custom support, or compliance
commitment. Commercial terms for the tested €299 internal-use offer must be
activated and reviewed before accepting the first payment. See
[the evaluation notice](EULA_PRO.md).
