#!/usr/bin/env bash
set -euo pipefail

API_URL="${API_URL:-http://localhost:8000}"
ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
OUT_DIR="$ROOT_DIR/examples/send-invoice/out"
PDF_INPUT="$ROOT_DIR/examples/invoice_raw.pdf"
METADATA_INPUT="$ROOT_DIR/examples/simple_invoice.json"
PDF_OUTPUT="$OUT_DIR/generated-facturx.pdf"
VALIDATION_OUTPUT="$OUT_DIR/validation.json"

if [ ! -f "$PDF_INPUT" ]; then
  echo "Missing input PDF: $PDF_INPUT" >&2
  exit 1
fi

if [ ! -f "$METADATA_INPUT" ]; then
  echo "Missing metadata JSON: $METADATA_INPUT" >&2
  exit 1
fi

mkdir -p "$OUT_DIR"

curl -sS -X POST "$API_URL/v1/convert" \
  -F "pdf=@$PDF_INPUT" \
  -F "metadata=@$METADATA_INPUT" \
  --output "$PDF_OUTPUT"

curl -sS -X POST "$API_URL/v1/validate" \
  -F "file=@$PDF_OUTPUT" \
  -o "$VALIDATION_OUTPUT"

echo "Generated: $PDF_OUTPUT"
echo "Validated: $VALIDATION_OUTPUT"
