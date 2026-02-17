import unittest
from unittest.mock import patch
from fastapi import UploadFile
from io import BytesIO

from app.api import validate_facturx

class TestSmartDiagnostics(unittest.TestCase):
    @patch.dict('os.environ', {'LICENSE_KEY': 'test_license_key'})
    @patch('app.license.is_licensed', return_value=True)
    @patch('app.services.hybrid_validation_service.HybridValidationService')
    @patch('app.metrics.metrics')
    def test_pro_gets_smart_diagnostics(self, mock_metrics, mock_hybrid_service, mock_is_licensed):
        """Pro users should receive ProValidationResult with diagnostics."""
        
        # Simulate a validation result with errors matching known rules
        mock_result = {
            "is_valid": False,
            "format_detected": "factur-x",
            "profile_detected": "en16931",
            "errors": [
                {"rule_id": "BR-CO-10", "message": "VAT total mismatch"},
                {"rule_id": "BR-01", "message": "Missing invoice number"},
                {"rule_id": "UNKNOWN-RULE", "message": "Some unknown error"}
            ]
        }
        mock_hybrid_service.validate.return_value = mock_result
        
        # Create a dummy file
        dummy_file = UploadFile(filename="invoice.pdf", file=BytesIO(b"%PDF-1.4..."))
        
        # Call the API endpoint logic directly
        response = validate_facturx(file=dummy_file)
        
        # Assertions
        print(f"Response Type: {type(response).__name__}")
        print(f"Validation Mode: {response.validation_mode}")
        
        self.assertEqual(response.validation_mode, "pro_smart_diagnostics")
        self.assertEqual(len(response.diagnostics), 3)
        
        # Check first diagnostic (BR-CO-10)
        d1 = response.diagnostics[0]
        print(f"\nDiagnostic 1: {d1.rule_id}")
        print(f"  Title: {d1.title}")
        self.assertEqual(d1.rule_id, "BR-CO-10")
        self.assertEqual(d1.title, "VAT Total Calculation Error")
        
        # Check second diagnostic (BR-01)
        d2 = response.diagnostics[1]
        print(f"\nDiagnostic 2: {d2.rule_id}")
        self.assertEqual(d2.rule_id, "BR-01")
        self.assertEqual(d2.title, "Missing Invoice Number")
        
        # Check third diagnostic (Fallback for unknown rule)
        d3 = response.diagnostics[2]
        print(f"\nDiagnostic 3: {d3.rule_id}")
        self.assertEqual(d3.rule_id, "UNKNOWN-RULE")
        self.assertIn("Validation Error", d3.title)
        
        print("\n✅ TEST PASSED: Pro users receive Smart Diagnostics!")

if __name__ == "__main__":
    unittest.main()
