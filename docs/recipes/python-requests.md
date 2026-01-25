# Recipe: Python (Requests)

How to integrate **Factur-X Engine** in your Python applications (FastAPI, Django, Flask).

## Prerequisites

- Python 3.x
- `requests` library (`pip install requests`)
- Factur-X Engine running on `http://localhost:8000`

## Implementation

```python
import requests

def generate_invoice(pdf_path, json_metadata):
    url = "http://localhost:8000/v1/convert"
    
    files = {
        'pdf': open(pdf_path, 'rb'),
    }
    data = {
        'metadata': json_metadata
    }

    response = requests.post(url, files=files, data=data)
    
    if response.status_code == 200:
        with open("factur-x-invoice.pdf", "wb") as f:
            f.write(response.content)
        print("Success: Generated factur-x-invoice.pdf")
    else:
        print(f"Error: {response.status_code}")
        print(response.text)

# Example Usage
metadata = """
{
    "invoice_id": "INV-2026-001",
    "seller": { "name": "Python Dev", "vat_id": "FR123456789" },
    "totals": { "net_amount": 100.00, "tax_amount": 20.00 }
}
"""
generate_invoice("input.pdf", metadata)
```

## Why this is better than local libraries?

- **No dependency conflict**: Avoids `lxml`, `reportlab` or `pypdf` version mismatches in your main app.
- **Iso-Prod**: The business logic (Schematron) is locked in the Docker container, ensuring identical results in dev and prod.
