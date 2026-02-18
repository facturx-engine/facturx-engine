import unittest
from lxml import etree
from app.services.validation_utils import detect_format, humanize_errors
from app.services.validator import ValidationService
from app.services.hybrid_validation_service import HybridValidationService

class TestValidationRefactor(unittest.TestCase):
    def test_utils_detect_format(self):
        # Basic CII
        xml = (
            b'<rsm:CrossIndustryInvoice '
            b'xmlns:rsm="urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100" '
            b'xmlns:ram="urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100">'
            b'<rsm:ExchangedDocumentContext>'
            b'<ram:GuidelineSpecifiedDocumentContextParameter>'
            b'<ram:ID>urn:cen.eu:en16931:2017</ram:ID>'
            b'</ram:GuidelineSpecifiedDocumentContextParameter>'
            b'</rsm:ExchangedDocumentContext>'
            b'</rsm:CrossIndustryInvoice>'
        )
        root = etree.fromstring(xml)
        fmt, level = detect_format(root)
        self.assertEqual(fmt, "factur-x")
        self.assertEqual(level, "en16931")

    def test_utils_humanize(self):
        errors = ["Some error about udt:DateTimeString", "Unknown error"]
        human = humanize_errors(errors)
        self.assertIn("Le format de la date est invalide", human[0])
        self.assertIn("Unknown error", human)

    def test_api_compatibility(self):
        # Ensure services still have the correct methods and don't crash on import/init
        self.assertTrue(hasattr(ValidationService, "validate_file"))
        self.assertTrue(hasattr(HybridValidationService, "validate"))
