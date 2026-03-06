# UBL 2.1 XSD — OASIS

## Missing files: `xsd/maindoc/UBL-Invoice-2.1.xsd` and `UBL-CreditNote-2.1.xsd`

This directory must contain the OASIS UBL 2.1 XSD schemas for structural validation.

### How to obtain them

1. Download the official OASIS UBL 2.1 package:
   https://docs.oasis-open.org/ubl/os-UBL-2.1/UBL-2.1.zip

2. Extract the archive and copy the **entire `xsd/` folder** here:
   ```
   app/resources/schemas/ubl-2.1/
   └── xsd/
       ├── common/           (shared component schemas)
       └── maindoc/
           ├── UBL-Invoice-2.1.xsd
           ├── UBL-CreditNote-2.1.xsd
           └── ... (other document types)
   ```

### Fallback behaviour

When these files are **absent**, `HybridValidationService` skips XSD structural validation
for UBL documents and applies Schematron (EN16931-UBL or XRechnung UBL) only.
The service logs a DEBUG-level message and continues normally.
