import os
import asyncio
import logging
from pathlib import Path

# Setup logging to see what happens
logging.basicConfig(level=logging.INFO)

# Set PYTHONPATH to include the current directory
sys_path = os.getcwd()
import sys
if sys_path not in sys.path:
    sys.path.append(sys_path)

from app.services.hybrid_validation_service import HybridValidationService

async def main():
    print("--- INTEGRATED v1.08 VALIDATION TEST ---")
    
    # Test file
    json_path = Path("examples/simple_invoice.json")
    if not json_path.exists():
        print(f"❌ Test file not found: {json_path}")
        return

    # To test validation, we need an XML. 
    # Since we can't easily convert JSON to XML without the whole engine, 
    # we'll use a pre-generated XML if it exists, or just try to validate the schemas.
    
    print("Verifying schema paths in HybridValidationService...")
    from app.services.hybrid_validation_service import XSD_PATH as ORIG_XSD, XSLT_PATH as ORIG_XSLT
    
    # OVERRIDE WITH TEMP PATHS (SANS ESPACES)
    XSD_PATH = Path("docs/v108_temp/Factur-X_1.08_EN16931.xsd").absolute()
    XSLT_PATH = Path("docs/v108_temp/_XSLT_EN16931/FACTUR-X_EN16931.xslt").absolute()
    
    print(f"XSD_PATH (Overridden): {XSD_PATH}")
    print(f"XSLT_PATH (Overridden): {XSLT_PATH}")
    
    if not XSD_PATH.exists():
        print("❌ XSD_PATH DOES NOT EXIST")
    else:
        print("✅ XSD_PATH exists")
        
    if not XSLT_PATH.exists():
        print("❌ XSLT_PATH DOES NOT EXIST")
    else:
        print("✅ XSLT_PATH exists")

    # Try a real validation of the schemas with dummy XML
    try:
        from app.services.hybrid_validator import HybridValidator
        validator = HybridValidator(xsd_path=str(XSD_PATH), xslt_path=str(XSLT_PATH))
        print("✅ HybridValidator instantiated successfully")
        
        # Minimal Factur-X XML for testing
        dummy_xml = b"""<?xml version="1.0" encoding="UTF-8"?>
<rsm:CrossIndustryInvoice xmlns:rsm="urn:un:unece:uncefact:data:standard:CrossIndustryInvoice:100" 
                         xmlns:ram="urn:un:unece:uncefact:data:standard:ReusableAggregateBusinessInformationEntity:100" 
                         xmlns:udt="urn:un:unece:uncefact:data:standard:UnqualifiedDataType:100">
    <rsm:ExchangedDocumentContext>
        <ram:GuidelineSpecifiedDocumentContextParameter>
            <ram:ID>urn:factur-x.eu:1p0:en16931</ram:ID>
        </ram:GuidelineSpecifiedDocumentContextParameter>
    </rsm:ExchangedDocumentContext>
</rsm:CrossIndustryInvoice>"""
        
        print("Running validator.validate()...")
        result = validator.validate(dummy_xml)
        print(f"Validation result: {'Valid' if result.is_valid else 'Invalid (as expected for dummy data)'}")
        print(f"XSD Valid: {result.xsd_valid}")
        print(f"Schematron Valid: {result.schematron_valid}")
        
        # If we got here without a crash, the engines (lxml/saxon) are working with the v1.08 files
        if result.xsd_valid is not None and result.schematron_valid is not None:
             print("✅ ENGINES ARE OPERATIONAL with v1.08 files")
        
    except Exception as e:
        print(f"❌ Validation cycle FAILED: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(main())
