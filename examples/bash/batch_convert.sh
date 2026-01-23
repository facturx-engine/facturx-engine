#!/bin/bash
# Batch convert all PDFs in current directory to Factur-X

API_URL="http://localhost:8000/v1/convert"
# Minimal metadata for demo
METADATA='{"invoice_number": "DEMO-123", "buyer": {"name": "Demo Client"}, "amounts": {"grand_total": "100.00"}}'

mkdir -p output

count=0
for file in *.pdf; do
    [ -e "$file" ] || continue
    echo "Processing $file..."
    curl -s -X POST "$API_URL" \
      -F "pdf=@$file" \
      -F "metadata=$METADATA" \
      --output "output/fx_$file"
    
    if [ $? -eq 0 ]; then
        echo "✅ Generated: output/fx_$file"
        ((count++))
    else
        echo "❌ Failed to convert $file"
    fi
done

if [ $count -eq 0 ]; then
    echo "No PDF files found in current directory."
fi
