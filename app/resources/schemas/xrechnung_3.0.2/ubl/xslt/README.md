# XRechnung 3.0.2 — UBL Schematron

## Missing file: `XRechnung-UBL-validation.xsl`

This directory must contain the compiled XRechnung UBL Schematron stylesheet.

### How to obtain it

1. Go to the KoSIT **xrechnung-schematron** releases page:
   https://github.com/itplr-kosit/xrechnung-schematron/releases

2. Download the release archive matching XRechnung **3.0.2**
   (e.g. `xrechnung-3.0.2-schematron-YYYY-MM-DD.zip`)

3. Inside the archive, locate:
   `xrechnung/ubl/xsl/XRechnung-UBL-validation.xsl`
   (exact path may vary by release)

4. Copy it here as:
   `app/resources/schemas/xrechnung_3.0.2/ubl/xslt/XRechnung-UBL-validation.xsl`

### Fallback behaviour

When this file is **absent**, `HybridValidationService` automatically falls back to
the EN16931-UBL Schematron (`_XSLT_EN16931_UBL/EN16931-UBL-validation.xslt`).
EN16931 base rules are still enforced; only XRechnung-specific rules (BR-DE-*, Leitweg-ID)
are skipped until the file is placed here.
