import unittest
from unittest.mock import patch
from app.services.generator import GeneratorService
from app.schemas.validation import InvoiceMetadata

class TestGeneratorService(unittest.TestCase):
    @patch('app.services.generator.generate_from_binary')
    @patch('app.services.hybrid_validation_service.HybridValidationService')
    def test_validation_uses_xml_bytes(self, mock_validation_service_cls, mock_generate_from_binary):
        # Setup
        # The class has a static method validate, so we mock that
        mock_validation_service_cls.validate.return_value = {"is_valid": True}
        mock_generate_from_binary.return_value = b"%PDF-1.4..." # Fake PDF

        # Minimal valid metadata
        metadata_dict = {
            "invoice_number": "TEST-OPT-001",
            "issue_date": "20240113",
            "seller": {
                "name": "Seller",
                "country_code": "FR",
                "address": {
                    "line1": "Street",
                    "postcode": "75001",
                    "city": "Paris",
                    "country_code": "FR"
                }
            },
            "buyer": {
                "name": "Buyer",
                "country_code": "FR",
                "address": {
                    "line1": "Street",
                    "postcode": "75002",
                    "city": "Paris",
                    "country_code": "FR"
                }
            },
            "amounts": {
                "tax_basis_total": "100.00",
                "tax_total": "20.00",
                "grand_total": "120.00",
                "due_payable": "120.00"
            },
            "currency_code": "EUR",
            "profile": "minimum"
        }
        metadata = InvoiceMetadata(**metadata_dict)
        pdf_content = b"%PDF-1.4 original"

        # Execute
        GeneratorService.generate_facturx_pdf(pdf_content, metadata)

        # Verify
        # Check that validate was called
        self.assertTrue(mock_validation_service_cls.validate.called)

        # Check arguments: (xml_bytes, filename)
        args, _ = mock_validation_service_cls.validate.call_args
        xml_bytes_arg = args[0]
        filename_arg = args[1]

        # Ensure we are passing bytes (XML content)
        self.assertIsInstance(xml_bytes_arg, bytes)
        # Ensure it is XML content (starts with <)
        self.assertTrue(xml_bytes_arg.strip().startswith(b'<'))

        # CRITICAL: Ensure filename ends with .xml to skip PDF extraction
        self.assertTrue(filename_arg.endswith('.xml'), f"Filename was {filename_arg}, expected to end with .xml")
        self.assertEqual(filename_arg, "generated_check.xml")

if __name__ == "__main__":
    unittest.main()
