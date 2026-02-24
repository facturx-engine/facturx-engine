import unittest
from unittest.mock import patch
from fastapi.testclient import TestClient
from pathlib import Path
import os
import json

from app.main import app

class TestSerialization(unittest.TestCase):
    def setUp(self):
        self.client = TestClient(app)
        print("DEBUG_ROUTES:", [route.path for route in app.routes])

    @patch('app.license.has_tier', return_value=False)
    @patch('app.metrics.metrics')
    def test_serialize_requires_license_403(self, mock_metrics, mock_has_tier):
        """Without a pro tier license, /serialize should return 403."""
        
        xml_content = b"""<?xml version="1.0" encoding="UTF-8"?>
        <rsm:CrossIndustryInvoice xmlns:rsm="urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100" 
                                 xmlns:ram="urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100">
            <rsm:ExchangedDocument><ram:ID>INV-123</ram:ID></rsm:ExchangedDocument>
            <rsm:ExchangedDocumentContext>
                <ram:GuidelineSpecifiedDocumentContextParameter>
                    <ram:ID>urn:cen.eu:en16931:2017</ram:ID>
                </ram:GuidelineSpecifiedDocumentContextParameter>
            </rsm:ExchangedDocumentContext>
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
        
        response = self.client.post(
            "/v1/serialize",
            files={"file": ("test.xml", xml_content, "application/xml")}
        )
        data = response.json()
        self.assertEqual(response.status_code, 403)
        self.assertEqual(data["type"], "urn:facturx:error:license_required")

    @patch('app.license.is_licensed', return_value=True)
    @patch('app.license.has_tier', return_value=True)
    @patch('app.metrics.metrics')
    def test_serialize_ubl_xrechnung(self, mock_metrics, mock_has_tier, mock_is_licensed):
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
            
            response = self.client.post(
                "/v1/serialize",
                files={"file": (ubl_file.name, content, "application/xml")}
            )

            if response.status_code != 200:
                print(f"DEBUG_TEST: UBL file serialization failed: {response.text}")

            self.assertEqual(response.status_code, 200)
            data = response.json()

            if not data.get("success"):
                self.fail(f"UBL file serialization failed. Response: {json.dumps(data, indent=2)}")
            
            self.assertTrue(data["success"])
            self.assertEqual(data["invoice"]["format"], "ubl")
            self.assertTrue(data["invoice"]["profile"].startswith("xrechnung"))
            
            # Basic assertions to ensure data is extracted
            self.assertIsNotNone(data["invoice"]["invoice_number"])
            self.assertGreater(float(data["invoice"]["total_gross_amount"]), 0)

if __name__ == "__main__":
    unittest.main()
