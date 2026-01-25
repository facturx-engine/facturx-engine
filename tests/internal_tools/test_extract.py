import requests
import json
import sys
import os

API_URL = "http://localhost:8000"
INPUT_PDF = "verify_output.pdf"

if not os.path.exists(INPUT_PDF):
    print(f"Error: {INPUT_PDF} not found. Run verification first.")
    sys.exit(1)

print(f"Testing /v1/extract with {INPUT_PDF}...")

try:
    with open(INPUT_PDF, "rb") as f:
        response = requests.post(f"{API_URL}/v1/extract", files={"file": f})
        
    if response.status_code == 200:
        data = response.json()
        print("[OK] Extraction Successful")
        print(json.dumps(data, indent=2))
        
        # Simple assertions
        if data.get("xml_extracted") is True:
            print("[OK] XML Extracted")
        else:
            print("[FAIL] XML Extraction Failed")
            
        if data.get("invoice_json"):
            print("[OK] Invoice Data Parsed")
        else:
            print("[FAIL] Invoice Data Missing")
            
    else:
        print(f"[FAIL] Failed: HTTP {response.status_code}")
        print(response.text)

except Exception as e:
    print(f"[ERROR] Error: {e}")
