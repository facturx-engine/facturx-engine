import sys
import os
from pathlib import Path

# Add project root to path
sys.path.append(os.getcwd())

from app.services.hybrid_validation_service import HybridValidationService

def test_file(file_path):
    print(f"Testing file: {file_path}")
    path = Path(file_path)
    if not path.exists():
        print(f"❌ File not found: {file_path}")
        return

    with open(path, "rb") as f:
        content = f.read()

    print(f"File size: {len(content)} bytes")
    
    # Run validation
    result = HybridValidationService.validate(content, path.name)
    
    print("\n--- Validation Result ---")
    print(f"Valid: {result['is_valid']}")
    print(f"Format: {result.get('format_detected')}")
    print(f"Profile: {result.get('profile_detected')}")
    print(f"Mode: {result.get('validation_mode')}")
    
    if result['errors']:
        print(f"\nErrors ({len(result['errors'])}):")
        for err in result['errors']:
            print(f"- [{err.get('rule_id', 'N/A')}] {err.get('message')}")
    else:
        print("\n✅ No errors found.")

if __name__ == "__main__":
    file_path = r"C:\Users\pasca\Downloads\ZUGFeRD-2.4-examples\_ZUGFeRD 2.4 examples\4. EXTENDED\EXTENDED_Fremdwaehrung\EXTENDED_Fremdwaehrung.pdf"
    test_file(file_path)
