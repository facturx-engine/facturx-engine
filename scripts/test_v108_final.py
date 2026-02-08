import os
import asyncio
import logging
from pathlib import Path

logging.basicConfig(level=logging.INFO)

# Set PYTHONPATH
import sys
sys_path = os.getcwd()
if sys_path not in sys.path:
    sys.path.append(sys_path)

from app.services.hybrid_validation_service import HybridValidationService, XSD_PATH, XSLT_PATH

async def main():
    print("=== FINAL v1.08 VALIDATION TEST (OFFICIAL PATHS) ===\n")
    
    print(f"XSD_PATH:  {XSD_PATH}")
    print(f"XSLT_PATH: {XSLT_PATH}\n")
    
    if not XSD_PATH.exists():
        print(f"❌ XSD NOT FOUND: {XSD_PATH}")
        return
    if not XSLT_PATH.exists():
        print(f"❌ XSLT NOT FOUND: {XSLT_PATH}")
        return
    
    print("✅ Both schema files exist\n")
    
    # Test with a minimal but structurally valid Factur-X fragment
    test_xml = b"""<?xml version="1.0" encoding="UTF-8"?>
<rsm:CrossIndustryInvoice xmlns:rsm="urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100" 
                         xmlns:ram="urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100" 
                         xmlns:udt="urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100">
    <rsm:ExchangedDocumentContext>
        <ram:GuidelineSpecifiedDocumentContextParameter>
            <ram:ID>urn:factur-x.eu:1p0:en16931</ram:ID>
        </ram:GuidelineSpecifiedDocumentContextParameter>
    </rsm:ExchangedDocumentContext>
</rsm:CrossIndustryInvoice>"""
    
    print("Running HybridValidationService.validate()...")
    result = HybridValidationService.validate(test_xml, "test.xml")
    
    print(f"\nValidation Mode: {result.get('validation_mode')}")
    print(f"XSD Valid: {result.get('xsd_valid')}")
    print(f"Schematron Valid: {result.get('schematron_valid')}")
    print(f"Overall Valid: {result.get('is_valid')}")
    
    if result.get("errors"):
        print(f"\nErrors ({len(result['errors'])}):")
        for err in result["errors"][:5]:  # Show first 5 errors
            print(f"  [{err.get('severity', 'error').upper()}] {err.get('rule_id')}: {err.get('message', '')[:80]}...")
    
    # Success criteria: engines run without crashes
    if result.get("xsd_valid") is not None and result.get("schematron_valid") is not None:
        print("\n" + "="*60)
        print("✅ SUCCESS: v1.08 schemas are OPERATIONAL")
        print("="*60)
        return True
    else:
        print("\n❌ FAILED: Validation did not complete")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)
