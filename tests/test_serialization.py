import unittest
import asyncio
import os
from unittest.mock import patch
from fastapi import UploadFile
from io import BytesIO
from decimal import Decimal
from pathlib import Path

from app.api import serialize_facturx


def run_async(coro):
    """Helper to run an async coroutine in tests."""
    return asyncio.get_event_loop().run_until_complete(coro)


class TestSerialization(unittest.TestCase):
    @patch('app.license.is_licensed', return_value=False)
    @patch('app.metrics.metrics')
    def test_serialize_trial_file_unlocked(self, mock_metrics, mock_is_licensed):
        """Whitelisted file should return full data in /serialize."""
        
        # Mock trial check to return True
        with patch('app.services.trial_service.is_trial_file', return_value=True):
            # Sample CII XML (Minimal)
            xml_content = b"""<?xml version="1.0" encoding="UTF-8"?>
            <rsm:CrossIndustryInvoice xmlns:rsm="urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100" 
                                     xmlns:ram="urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100">
                <rsm:ExchangedDocument><ram:ID>INV-123</ram:ID></rsm:ExchangedDocument>
                <rsm:SupplyChainTradeTransaction>
                    <ram:ApplicableHeaderTradeAgreement>
                        <ram:SellerTradeParty><ram:Name>Acme Corp</ram:Name></ram:SellerTradeParty>
                        <ram:BuyerTradeParty><ram:Name>Global Industries</ram:Name></ram:BuyerTradeParty>
                    </ram:ApplicableHeaderTradeAgreement>
                    <ram:ApplicableHeaderTradeSettlement>
                        <ram:SpecifiedTradeSettlementHeaderMonetarySummation>
                            <ram:TaxBasisTotalAmount>100.00</ram:TaxBasisTotalAmount>
                            <ram:TaxTotalAmount>20.00</ram:TaxTotalAmount>
                            <ram:GrandTotalAmount>120.00</ram:GrandTotalAmount>
                            <ram:DuePayableAmount>120.00</ram:DuePayableAmount>
                        </ram:SpecifiedTradeSettlementHeaderMonetarySummation>
                    </ram:ApplicableHeaderTradeSettlement>
                </rsm:SupplyChainTradeTransaction>
            </rsm:CrossIndustryInvoice>"""
            
            dummy_file = UploadFile(filename="test.xml", file=BytesIO(xml_content))
            
            response = run_async(serialize_facturx(file=dummy_file))
            
            self.assertTrue(response.success)
            self.assertEqual(response.invoice.invoice_number, "INV-123")
            self.assertEqual(response.invoice.seller.name, "Acme Corp")
            self.assertEqual(response.invoice.total_gross_amount, Decimal("120.00"))
            self.assertFalse(response.invoice.is_obfuscated)
            self.assertIn("Trial Mode", response.trial_notice)

    @patch('app.license.is_licensed', return_value=False)
    @patch('app.metrics.metrics')
    def test_serialize_normal_file_obfuscated(self, mock_metrics, mock_is_licensed):
        """Normal file should return masked data in /serialize for Community users."""
        
        with patch('app.services.trial_service.is_trial_file', return_value=False):
            xml_content = b"""<?xml version="1.0" encoding="UTF-8"?>
            <rsm:CrossIndustryInvoice xmlns:rsm="urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100" 
                                     xmlns:ram="urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100">
                <rsm:ExchangedDocument><ram:ID>INV-123</ram:ID></rsm:ExchangedDocument>
                <rsm:SupplyChainTradeTransaction>
                    <ram:ApplicableHeaderTradeAgreement>
                        <ram:SellerTradeParty><ram:Name>Acme Corp</ram:Name></ram:SellerTradeParty>
                        <ram:BuyerTradeParty><ram:Name>Global Industries</ram:Name></ram:BuyerTradeParty>
                    </ram:ApplicableHeaderTradeAgreement>
                    <ram:ApplicableHeaderTradeSettlement>
                        <ram:SpecifiedTradeSettlementHeaderMonetarySummation>
                            <ram:TaxBasisTotalAmount>100.00</ram:TaxBasisTotalAmount>
                        </ram:SpecifiedTradeSettlementHeaderMonetarySummation>
                    </ram:ApplicableHeaderTradeSettlement>
                </rsm:SupplyChainTradeTransaction>
            </rsm:CrossIndustryInvoice>"""
            
            dummy_file = UploadFile(filename="private.xml", file=BytesIO(xml_content))
            
            response = run_async(serialize_facturx(file=dummy_file))
            
            self.assertTrue(response.success)
            self.assertTrue(response.invoice.is_obfuscated)
            # Acme Corp -> Ac*******
            self.assertEqual(response.invoice.seller.name, "Ac*******")
            self.assertEqual(response.invoice.total_net_amount, Decimal("0.00"))
            self.assertIn("Community Mode", response.trial_notice)

    @patch('app.license.is_licensed', return_value=True)
    @patch('app.metrics.metrics')
    def test_serialize_ubl_xrechnung(self, mock_metrics, mock_is_licensed):
        """Pro users should be able to serialize UBL (XRechnung) files."""
        
        # We must simulate a License Key being present to trigger the is_licensed check
        with patch.dict(os.environ, {"LICENSE_KEY": "valid-key"}):
            # Find a real UBL file in the corpus
            corpus_dir = Path(__file__).parent / "corpus" / "xrechnung-3.0.2-testsuite-2025-07-10" / "instances"
            ubl_file = None
            for f in corpus_dir.rglob("*.xml"):
                if b"CrossIndustryInvoice" not in f.read_bytes()[:500]:
                    ubl_file = f
                    break
            
            if not ubl_file:
                self.skipTest("No UBL file found in corpus for testing")

            print(f"Testing UBL serialization with: {ubl_file.name}")
            content = ubl_file.read_bytes()
            dummy_file = UploadFile(filename=ubl_file.name, file=BytesIO(content))

            # Run serialization (Pro mode unlocked via mock)
            response = run_async(serialize_facturx(file=dummy_file))

            self.assertTrue(response.success)
            self.assertEqual(response.invoice.format, "ubl")
            self.assertEqual(response.invoice.profile, "xrechnung")
            
            # Basic assertions to ensure data is extracted
            self.assertIsNotNone(response.invoice.invoice_number)
            self.assertGreater(response.invoice.total_gross_amount, 0)
            self.assertFalse(response.invoice.is_obfuscated)


if __name__ == "__main__":
    unittest.main()
