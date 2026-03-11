#!/usr/bin/env bash
set -euo pipefail

API_URL="${API_URL:-http://localhost:8000}"
ROOT_DIR="$(cd "$(dirname "$0")/../.." && pwd)"
OUT_DIR="$ROOT_DIR/examples/receive-invoice/out"
INPUT_FILE="${1:-$ROOT_DIR/examples/send-invoice/out/generated-facturx.pdf}"
VALIDATION_OUTPUT="$OUT_DIR/validation.json"
EXTRACT_OUTPUT="$OUT_DIR/extract.json"
SERIALIZE_OUTPUT="$OUT_DIR/serialize.json"

if [ ! -f "$INPUT_FILE" ]; then
  echo "Missing input invoice: $INPUT_FILE" >&2
  echo "Run examples/send-invoice/run.sh first or pass a PDF/XML path as the first argument." >&2
  exit 1
fi
SERIALIZE_ERROR_OUTPUT="$OUT_DIR/serialize-error.json"

mkdir -p "$OUT_DIR"

curl -sS -X POST "$API_URL/v1/validate" \
  -F "file=@$INPUT_FILE" \
  -o "$VALIDATION_OUTPUT"

curl -sS -X POST "$API_URL/v1/extract" \
  -F "file=@$INPUT_FILE" \
  -o "$EXTRACT_OUTPUT"

HTTP_CODE="$(curl -sS -o "$SERIALIZE_OUTPUT" -w "%{http_code}" -X POST "$API_URL/v1/serialize" \
  -F "file=@$INPUT_FILE")"

if [ "$HTTP_CODE" != "200" ]; then
  mv "$SERIALIZE_OUTPUT" "$SERIALIZE_ERROR_OUTPUT"
  echo "Serialize unavailable (HTTP $HTTP_CODE). See: $SERIALIZE_ERROR_OUTPUT"
else
  echo "Serialized: $SERIALIZE_OUTPUT"
fi

echo "Validated: $VALIDATION_OUTPUT"
echo "Extracted: $EXTRACT_OUTPUT"
