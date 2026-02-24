import unittest
from fastapi.testclient import TestClient
import os
from unittest.mock import patch
from app.main import app

class TestEndToEndWorkflows(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        self.invoice_path = "tests/corpus/valid/Facture_FR_MINIMUM.pdf"
        with open(self.invoice_path, "rb") as f:
            self.invoice_content = f.read()

    def test_community_workflow(self):
        """Workflow for a user WITHOUT a license key and NO trial file."""
        with patch.dict(os.environ, {"LICENSE_KEY": ""}):
            with patch("app.license.is_licensed", return_value=False):
                with patch("app.services.trial_service.is_trial_file", return_value=False):
                    files = {"file": ("test.pdf", self.invoice_content, "application/pdf")}
                    response = self.client.post("/v1/validate", files=files)
                    data = response.json()
                    
                    self.assertEqual(response.status_code, 200)
                    self.assertEqual(data["validation_mode"], "open_community")
                    self.assertIn("errors", data)
                    self.assertNotIn("diagnostics", data)

                    # Test Serialization
                    response = self.client.post("/v1/serialize", files=files)
                    self.assertEqual(response.status_code, 403)

    def test_pro_workflow(self):
        """Workflow for a user WITH a valid license key."""
        with patch.dict(os.environ, {"LICENSE_KEY": "PRO-VALID-KEY"}):
            with patch("app.license.is_licensed", return_value=True):
                with patch("app.license.has_tier", return_value=True):
                    with patch("app.services.trial_service.is_trial_file", return_value=False):
                        files = {"file": ("test.pdf", self.invoice_content, "application/pdf")}
                        
                        # 1. Test Validation
                        response = self.client.post("/v1/validate", files=files)
                        data = response.json()
                        self.assertEqual(data["validation_mode"], "pro_smart_diagnostics")
                        self.assertIn("diagnostics", data)
                        # 2. Test Serialization
                        response = self.client.post("/v1/serialize", files=files)
                        data = response.json()
                        self.assertTrue(data["success"])



if __name__ == "__main__":
    unittest.main()
