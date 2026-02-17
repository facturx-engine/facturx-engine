import unittest
from unittest.mock import patch
from fastapi import UploadFile
from io import BytesIO

from app.api import validate_facturx

class TestTrialMode(unittest.TestCase):
    @patch('app.license.is_licensed', return_value=False) # No license
    @patch('app.services.hybrid_validation_service.HybridValidationService')
    @patch('app.metrics.metrics')
    def test_trial_file_unlocks_pro_features(self, mock_metrics, mock_hybrid_service, mock_is_licensed):
        """A whitelisted trial file should unlock Pro features without a license."""
        
        # 1. Use a hash from the whitelist
        # We need to simulate the content that produces one of these hashes
        # Facture_FR_MINIMUM.pdf hash: a0db0603cea39130ce4fd5ad56c2f5a1
        # Since we use MD5, we can't easily reverse it, but we can MOCK `is_trial_file` 
        # OR just use a known file content if we had one.
        # Let's mock `is_trial_file` for simplicity in the unit test, 
        # as we've already verified the hashes match the files in the corpus.
        
        with patch('app.services.trial_service.is_trial_file', return_value=True):
            # Simulate a validation result
            mock_result = {
                "is_valid": False,
                "format_detected": "factur-x",
                "profile_detected": "en16931",
                "errors": [{"rule_id": "BR-CO-10", "message": "VAT total mismatch"}]
            }
            mock_hybrid_service.validate.return_value = mock_result
            
            # Create a dummy file
            dummy_file = UploadFile(filename="demo_invoice.pdf", file=BytesIO(b"dummy content"))
            
            # Call the API
            response = validate_facturx(file=dummy_file)
            
            # Assertions
            print(f"Validation Mode: {response.validation_mode}")
            print(f"Trial Notice: {response.trial_notice}")
            
            self.assertEqual(response.validation_mode, "pro_smart_diagnostics")
            self.assertIn("Trial Mode", response.trial_notice)
            self.assertTrue(len(response.diagnostics) > 0)
            self.assertEqual(response.diagnostics[0].rule_id, "BR-CO-10")

    @patch('app.license.is_licensed', return_value=False)
    @patch('app.services.hybrid_validation_service.HybridValidationService')
    @patch('app.metrics.metrics')
    def test_normal_file_stays_community(self, mock_metrics, mock_hybrid_service, mock_is_licensed):
        """A normal (non-whitelisted) file should stay in Community mode without a license."""
        
        with patch('app.services.trial_service.is_trial_file', return_value=False):
            mock_result = {
                "is_valid": False,
                "format_detected": "factur-x",
                "profile_detected": "en16931",
                "errors": [{"rule_id": "BR-CO-10", "message": "VAT total mismatch"}]
            }
            mock_hybrid_service.validate.return_value = mock_result
            
            dummy_file = UploadFile(filename="my_invoice.pdf", file=BytesIO(b"my private content"))
            
            response = validate_facturx(file=dummy_file)
            
            print(f"Validation Mode: {response.validation_mode}")
            self.assertEqual(response.validation_mode, "open_community")
            self.assertIsNone(response.trial_notice)
            # Should have raw errors, not diagnostics
            self.assertTrue(hasattr(response, 'errors'))
            self.assertFalse(hasattr(response, 'diagnostics'))

if __name__ == "__main__":
    unittest.main()
