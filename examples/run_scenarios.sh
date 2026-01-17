#!/bin/bash
# Note: Ensure you have a 'dummy.pdf' in this folder to act as the base PDF.

echo "--- 1. Generating Simple Invoice ---"
curl -X 'POST' \
  'http://localhost:8000/v1/convert' \
  -F 'pdf=@dummy.pdf' \
  -F 'metadata=<simple_invoice.json' \
  -o result_simple.pdf

echo "\n--- 2. Validating Simple Invoice ---"
curl -X 'POST' \
  'http://localhost:8000/v1/validate' \
  -F 'file=@result_simple.pdf'

echo "\n\n--- 3. Generating Complex Multi-VAT Invoice ---"
curl -X 'POST' \
  'http://localhost:8000/v1/convert' \
  -F 'pdf=@dummy.pdf' \
  -F 'metadata=<complex_multi_vat.json' \
  -o result_complex.pdf

echo "\n--- 4. Validating Complex Invoice ---"
curl -X 'POST' \
  'http://localhost:8000/v1/validate' \
  -F 'file=@result_complex.pdf'
