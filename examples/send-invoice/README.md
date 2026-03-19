# Showcase: Send Invoice

This example shows the outbound path used by ERP and billing integrations.

It answers three questions:
- Can the engine turn ERP JSON into a Factur-X PDF?
- What is the minimum payload to get a valid result?
- How do we verify the generated output without over-claiming PDF/A?

## Prerequisites

Start the API locally:

```bash
docker run -d -p 8000:8000 facturxengine/facturx-engine:latest
```

## Inputs used by this example

- Source PDF: `../invoice_raw.pdf`
- Metadata: `../simple_invoice.json`
- Output folder: `./out/`

## Run it

From the repository root:

```bash
bash examples/send-invoice/run.sh
```

The script will:
- call `/v1/convert`
- write `examples/send-invoice/out/generated-facturx.pdf`
- call `/v1/validate` on the generated file
- write `examples/send-invoice/out/validation.json`

## What to inspect

Open `examples/send-invoice/out/validation.json` and check:
- `valid`
- `validation_completeness`
- `pdfa_valid`
- `layers_executed`
- `layers_skipped`

Important:
- `pdfa_valid = true` only means VeraPDF ran and the output passed.
- `pdfa_valid = null` means PDF/A was not verified, not that the file failed.
- `/v1/convert` generates the output, but `/v1/validate` is the proof step.

## Manual curl version

```bash
curl -X POST "http://localhost:8000/v1/convert" \
  -F "pdf=@examples/invoice_raw.pdf" \
  -F "metadata=@examples/simple_invoice.json" \
  --output examples/send-invoice/out/generated-facturx.pdf

curl -X POST "http://localhost:8000/v1/validate" \
  -F "file=@examples/send-invoice/out/generated-facturx.pdf" \
  -o examples/send-invoice/out/validation.json
```

## Next step

Once you have a generated Factur-X PDF, continue with [../receive-invoice/README.md](../receive-invoice/README.md) to test the inbound workflow on the same file.