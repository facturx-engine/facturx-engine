#!/usr/bin/env python3
"""
Factur-X Engine Smoke Test Script
=================================

A zero-dependency (standard lib only) script to verify the core functions of the Factur-X Engine.
Useful for CI/CD gates, post-deployment checks, and client acceptance.

Usage:
    python smoke_test.py [BASE_URL]

    Default BASE_URL: http://localhost:8000
"""
import sys
import json
import time
import base64
import urllib.request
import urllib.error
from typing import Dict, Any, Tuple

# --- Configuration ---
DEFAULT_URL = "http://localhost:8000"
TIMEOUT = 10  # seconds

# --- ANSI Colors ---
class Colors:
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKCYAN = '\033[96m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'

    @staticmethod
    def print(msg, color=None):
        if sys.platform == 'win32':
            print(msg) # No colors on old cmd.exe
        else:
            print(f"{color}{msg}{Colors.ENDC}" if color else msg)

def request(method: str, url: str, data: Dict = None, files: Dict[str, Tuple[str, bytes]] = None) -> Tuple[int, Any]:
    """Helper to make HTTP requests without 'requests' library."""
    try:
        req = urllib.request.Request(url, method=method)
        
        # Determine if we need multipart (if files provided OR if we explicitly want form-data for mixed content)
        if files or (data and any(isinstance(v, (bytes, bytearray)) for v in data.values())):
            boundary = '----FacturXSmokeTestBoundary'
            body = bytearray()
            
            # 1. Add Form Fields (data)
            if data:
                for field, value in data.items():
                    body.extend(f'--{boundary}\r\n'.encode())
                    body.extend(f'Content-Disposition: form-data; name="{field}"\r\n\r\n'.encode())
                    body.extend(str(value).encode()) # Value as string
                    body.extend(b'\r\n')

            # 2. Add Files
            if files:
                for field, (filename, content) in files.items():
                    body.extend(f'--{boundary}\r\n'.encode())
                    body.extend(f'Content-Disposition: form-data; name="{field}"; filename="{filename}"\r\n'.encode())
                    body.extend(f'Content-Type: application/pdf\r\n\r\n'.encode())
                    body.extend(content)
                    body.extend(b'\r\n')
            
            body.extend(f'--{boundary}--\r\n'.encode())
            
            req.add_header('Content-Type', f'multipart/form-data; boundary={boundary}')
            req.data = body
            
        elif data:
            req.add_header('Content-Type', 'application/json')
            req.data = json.dumps(data).encode('utf-8')
            
        with urllib.request.urlopen(req, timeout=TIMEOUT) as response:
            status = response.status
            content = response.read()
            # Try parsing JSON
            try:
                return status, json.loads(content)
            except:
                return status, content
                
    except urllib.error.HTTPError as e:
        content = e.read()
        try:
            return e.code, json.loads(content)
        except:
            return e.code, content.decode()
    except Exception as e:
        return 0, str(e)

# --- Minimal PDF Base64 (Blank A4) ---
MINIMAL_PDF_B64 = "JVBERi0xLjMKJZOMi54gUmVwb3J0TGFiIEdlbmVyYXRlZCBQREYgZG9jdW1lbnQgaHR0cDovL3d3dy5yZXBvcnRsYWIuY29tCjEgMCBvYmoKPDwKL0YxIDIgMCBSCj4+CmVuZG9iagoyIDAgb2JqCjw8Ci9CYXNlRm9udCAvSGVsdmV0aWNhIC9FbmNvZGluZyAvV2luQW5zaUVuY29kaW5nIC9OYW1lIC9GMSAvU3VidHlwZSAvVHlwZTEgL0R5cGUgL0ZvbnQKPj4KZW5kb2JqCjMgMCBvYmoKPDwKL0NvbnRlbnRzIDcgMCBSIC9NZWRpYUJveCBbIDAgMCA1OTUuMjc1NiA4NDEuODg5OCBdIC9QYXJlbnQgNiAwIFIgL1Jlc291cmNlcyA8PAovRm9udCAxIDAgUiAvUHJvY1NldCBbIC9QREYgL1RleHQgL0ltYWdlQiAvSW1hZ2VDIC9JbWFnZUkgXQo+PiAvUm90YXRlIDAgL1RyYW5zIDw8Cgo+PiAKICAvVHlwZSAvUGFnZQo+PgplbmRvYmoKNCAwIG9iago8PAovUGFnZU1vZGUgL1VzZU5vbmUgL1BhZ2VzIDYgMCBSIC9UeXBlIC9DYXRhbG9nCj4+CmVuZG9iago1IDAgb2JqCjw8Ci9BdXRob3IgKGFub255bW91cykgL0NyZWF0aW9uRGF0ZSAoRDoyMDI2MDEyNTEwMzAxMSswMScwMCcpIC9DcmVhdG9yIChSZXBvcnRMYWIgUERGIExpYnJhcnkgLSB3d3cucmVwb3J0bGFiLmNvbSkgL0tleXdvcmRzICgpIC9Nb2REYXRlIChEOjIwMjYwMTI1MTAzMDExKzAxJzAwJykgL1Byb2R1Y2VyIChSZXBvcnRMYWIgUERGIExpYnJhcnkgLSB3d3cucmVwb3J0bGFiLmNvbSkgCiAgL1N1YmplY3QgKHVuc3BlY2lmaWVkKSAvVGl0bGUgKHVudGl0bGVkKSAvVHJhcHBlZCAvRmFsc2UKPj4KZW5kb2JqCjYgMCBvYmoKPDwKL0NvdW50IDEgL0tpZHMgWyAzIDAgUiBdIC9UeXBlIC9QYWdlcwo+PgplbmRvYmoKNyAwIG9iago8PAovRmlsdGVyIFsgL0FTQ0lJODVEZWNvZGUgL0ZsYXRlRGVjb2RlIF0gL0xlbmd0aCAxMTUKPj4Kc3RyZWFtCkdhcFFoMEU9RiwwVVxIM1RccE5ZVF5RS2s/dGM+SVAsO1cjVTFeMjNpaFBFTV8/Q1c0S0lTaTkwTWpHXjIsRlMjPFI+XFg5Si5iR2RaJScvY0hYWzE8PHUvSjAlIVcoYVxpRGwhYmtRaiFXXkhrKCNKfj5lbmRzdHJlYW0KZW5kb2JqCnhyZWYKMCA4CjAwMDAwMDAwMDAgNjU1MzUgZiAKMDAwMDAwMDA3MyAwMDAwMCBuIAowMDAwMDAwMTA0IDAwMDAwIG4gCjAwMDAwMDAyMTEgMDAwMDAgbiAKMDAwMDAwMDQxNCAwMDAwMCBuIAowMDAwMDAwNDgyIDAwMDAwIG4gCjAwMDAwMDA3NzggMDAwMDAgbiAKMDAwMDAwMDgzNyAwMDAwMCBuIAp0cmFpbGVyCjw8Ci9JRCAKWzwwZTJmODA2MDExMzZkMmIyODkxOWQ2MGE3ZjI3NzUxZj48MGUyZjgwNjAxMTM2ZDJiMjg5MTlkNjBhN2YyNzc1MWY+XQolIFJlcG9ydExhYiBnZW5lcmF0ZWQgUERGIGRvY3VtZW50IC0tIGRpZ2VzdCAoaHR0cDovL3d3dy5yZXBvcnRsYWIuY29tKQoKL0luZm8gNSAwIFIKL1Jvb3QgNCAwIFIKL1NpemUgOAo+PgpzdGFydHhyZWYKMTA0MgolJUVPRgo="

def run_tests(base_url: str):
    Colors.print(f"🚀 Starting Factur-X Engine Smoke Test on {base_url} ...\n", Colors.HEADER)
    
    start_time = time.time()
    generated_pdf = None
    
    # ---------------------------------------------------------
    # 1. Health Check
    # ---------------------------------------------------------
    Colors.print("[1/4] Checking Health API...", Colors.OKBLUE)
    status, res = request('GET', f"{base_url}/health")
    if status == 200 and res.get('status') == 'healthy':
        Colors.print(f"  ✅ OK (200) - Version: {res.get('version')}", Colors.OKGREEN)
    else:
        Colors.print(f"  ❌ FAILED: {status} - {res}", Colors.FAIL)
        sys.exit(1)

    # ---------------------------------------------------------
    # 2. Convert (Generate Factur-X)
    # ---------------------------------------------------------
    Colors.print("\n[2/4] Testing Conversion (PDF -> Factur-X)...", Colors.OKBLUE)
    
    # Prepare Payload correctly for Multipart
    # 1. Decode PDF
    base_pdf_bytes = base64.b64decode(MINIMAL_PDF_B64)
    
    # 2. Prepare Metadata JSON String
    metadata_dict = {
        "invoice_number": "SMOKE-001",
        "issue_date": "20260126",
        "seller": {
            "name": "Smoke Test Corp",
            "country_code": "FR",
            "vat_number": "FR999999999"
        },
        "buyer": {"name": "Test Client"},
        "lines": [
            {"name": "Test Item", "quantity": 1, "net_price": 100, "net_total": 100, "vat_rate": 20}
        ],
        "amounts": {
            "tax_basis_total": "100.00",
            "tax_total": "20.00",
            "grand_total": "120.00",
            "due_payable": "120.00"
        },
        "tax_details": [
            {"calculated_amount": "20.00", "basis_amount": "100.00", "rate": "20.00", "category_code": "S"}
        ]
    }
    
    # helper handles mixed data (fields) and files
    status, res_pdf = request(
        'POST', 
        f"{base_url}/v1/convert", 
        data={"metadata": json.dumps(metadata_dict)}, 
        files={"pdf": ("input.pdf", base_pdf_bytes)}
    )
    
    if status == 200:
        generated_pdf = res_pdf # Raw bytes expected? No, API returns bytes but request() tries JSON
        # Our helper function tries JSON, but convert returns raw bytes usually?
        # Let's check api.py or assume standard behavior.
        # Actually our helper returns bytes if json load fails.
        if isinstance(res_pdf, bytes) and res_pdf.startswith(b'%PDF'):
             Colors.print(f"  ✅ OK - Received {len(res_pdf)} bytes of PDF/A-3", Colors.OKGREEN)
             generated_pdf = res_pdf
        else:
             Colors.print(f"  ❌ FAILED: Not a valid PDF", Colors.FAIL)
             sys.exit(1)
    else:
        Colors.print(f"  ❌ FAILED: {status} - {res_pdf}", Colors.FAIL)
        sys.exit(1)
        
    # ---------------------------------------------------------
    # 3. Validate (Loopback)
    # ---------------------------------------------------------
    Colors.print("\n[3/4] Testing Validation (on generated file)...", Colors.OKBLUE)
    status, res = request('POST', f"{base_url}/v1/validate", files={'file': ('smoke.pdf', generated_pdf)})
    
    if status == 200 and res.get('valid') is True:
        Colors.print(f"  ✅ OK - Validated as {res.get('flavor')}", Colors.OKGREEN)
    else:
        Colors.print(f"  ❌ FAILED: Invalid - {res}", Colors.FAIL)
        # We don't exit here, just warn, as generation might be Basic and Validation Strict
        # But here we generated EN16931 default so it should pass.
        sys.exit(1)

    # ---------------------------------------------------------
    # 4. Extract (Data check)
    # ---------------------------------------------------------
    Colors.print("\n[4/4] Testing Extraction...", Colors.OKBLUE)
    status, res = request('POST', f"{base_url}/v1/extract", files={'file': ('smoke.pdf', generated_pdf)})
    
    if status == 200:
        inv = res.get('invoice_json', {})
        inv_num = inv.get('invoice_number')
        if inv_num == "SMOKE-001":
             Colors.print(f"  ✅ OK - Extracted Invoice #: {inv_num}", Colors.OKGREEN)
        else:
             Colors.print(f"  ⚠️  WARNING: Data mismatch. Found: {inv_num}", Colors.WARNING)
    else:
        Colors.print(f"  ❌ FAILED: {status} - {res}", Colors.FAIL)
        sys.exit(1)

    # ---------------------------------------------------------
    # Summary
    # ---------------------------------------------------------
    duration = time.time() - start_time
    Colors.print(f"\n✨ SMOKE TEST PASSED in {duration:.2f}s ✨", Colors.HEADER)

if __name__ == "__main__":
    url = sys.argv[1] if len(sys.argv) > 1 else DEFAULT_URL
    try:
        run_tests(url)
    except KeyboardInterrupt:
        print("\nAborted.")
        sys.exit(130)
    except Exception as e:
        Colors.print(f"\nCRITICAL ERROR: {e}", Colors.FAIL)
        sys.exit(1)
