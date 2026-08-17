# Factur-X Engine Examples

These examples are optimized for technical evaluation.

Start here if you want to answer one of these questions quickly:
- Can this engine generate an outbound invoice artifact from ERP JSON?
- Can it validate and strictly normalize a supported inbound invoice?
- What does the API actually prove, and what stays heuristic?

## Showcase examples

- [send-invoice](send-invoice/README.md): generate a Factur-X PDF from a plain PDF plus JSON metadata, then re-validate the output.
- [receive-invoice](receive-invoice/README.md): validate an inbound Factur-X invoice, inspect the non-importable preview, and optionally call `/v1/serialize` for strict schema v2 JSON.

## Supporting assets

- [simple_invoice.json](simple_invoice.json): minimal outbound payload
- [complex_multi_vat.json](complex_multi_vat.json): multi-VAT outbound payload
- [invoice_raw.pdf](invoice_raw.pdf): plain PDF input for generation examples

## Trust-first reading order

1. Run [send-invoice](send-invoice/README.md) if you want to test outbound generation.
2. Run [receive-invoice](receive-invoice/README.md) if you want to test inbound validation and ERP normalization.
3. Read [../TRUST_MODEL.md](../TRUST_MODEL.md) to understand what each endpoint proves, what stays heuristic, and how to interpret `pdfa_valid`, `validation_completeness`, strict mapping statuses, and `_meta.limitations`.

## Legacy cookbook

The previous [COOKBOOKS.md](COOKBOOKS.md) file is still available, but the two showcase folders above are the recommended entry point for audits and evaluations.
