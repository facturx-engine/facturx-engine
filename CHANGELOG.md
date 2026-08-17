# Changelog - Factur-X API

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [2.0.0] - 2026-08-17

### Changed
- **Serialize**: Replace recovery and fallback mapping with the strict `2.0.0` ERP contract. Malformed, incomplete, unsupported, or not fully validated invoices now fail with HTTP 422 and stable diagnostics.
- **Extract**: Mark heuristic extraction explicitly as a non-importable `preview`.
- **Trust boundaries**: Document that validation reports technical checks only and that generation does not guarantee fiscal, regulatory, or recipient acceptance.
- **Operations**: Make Prometheus metrics opt-in through `METRICS_ENABLED=true` and `METRICS_TOKEN`, independently of commercial licensing.
- **Commercial status**: Replace inactive paid checkout links with the free Intake evaluation path and remove unsupported SLA, security-response, and compliance commitments.

### Legal
- **Repository license**: Restore an unmodified MIT license for all code published in this repository. The previous proprietary exceptions were incompatible with the repository-wide grant and have been removed.

## [1.8.3] - 2026-08-04

### Added
- **Validation**: Vendor the complete official OASIS UBL 2.1 XSD package and apply structural validation to UBL invoices and credit notes.
- **Validation**: Apply the bundled Factur-X 1.09 EXTENDED XSD before EXTENDED Schematron rules.

### Fixed
- **Release metadata**: Align the API version with the published release series.

## [1.8.2] - 2026-08-04

### Fixed
- **Security**: Update `pypdf` to 6.14.2 and remove build-only pip tooling from the runtime image.
- **Security**: Overlay Jackson 2.21.4 in the bundled VeraPDF runtime to remediate published Jackson findings.

## [1.8.1] - 2026-07-10

### Fixed
- **Validation**: Hardened Saxon-HE subprocess execution for BR-FR CTC validation by writing SVRL output to an explicit file, resolving XSLT/JAR paths absolutely, and running Saxon from the stylesheet directory.
- **Validation**: Correctly reads Schematron `flag` severity attributes in addition to `role`, matching the official French BR-FR CTC artifacts.
- **Compliance**: Updated runtime validation artifacts to FNFE `FNFE_RFE_INVOICE_1.4.0` and CEN EN 16931 validation artifacts `1.3.16`.
- **Compliance**: Added Factur-X `1.09` / ZUGFeRD `2.5` EN16931 and BASICWL XSD validation artifacts and switched runtime schema selection to the new XSDs.
- **Generation**: Added France 1.4.0 mapping support for `business_process_type` (BT-23), SIREN legal identifiers, and electronic routing addresses (BT-34/BT-49).
- **Compatibility**: Removed obsolete `check_schematron` arguments for `factur-x==4.2` generation and merge flows.
- **Extraction**: PDF XML extraction now accepts raw `bytes` as well as file-like streams.

### Changed
- **Dependencies**: Updated `python-multipart` to 0.0.30 and VeraPDF to 1.30.2 to clear current Trivy findings.
- **CI/CD**: Updated GitHub Actions to current Node 24-compatible releases, pinned Trivy, generated release SBOMs from the freshly built image digest, and signed images by digest with Cosign.

## [1.7.0] - 2026-03-10

### Added
- **Serialize**: `/v1/serialize` responses now include `fallbacks_applied` (always present, `[]` by default) and `xml_recovery_applied` fields for full fallback transparency.
- **Extract**: `/v1/extract` responses now include `_meta.limitations` listing heuristic behaviors (e.g. `max_20_lines_cii`, `fallback_values_used`).
- **Diagnostics**: `/diagnostics` endpoint now protected by `DIAGNOSTICS_TOKEN` (401/403 when exposed publicly).

### Changed
- **Healthz**: `not_configured` dependencies now return `degraded` instead of `healthy` on `/healthz`.
- **Wording**: All "DEMO" references replaced by "Community" in startup logs, extractor, and documentation.
- **Wording**: "SaxonC" replaced by "Saxon-HE" across all landing pages (EN/FR/DE).
- **Wording**: `/v1/serialize` documented as "normalized ERP integration JSON" instead of "direct database insertion".
- **Wording**: `/v1/extract` documented as "heuristic best-effort extraction" instead of "raw XML fields".
- **Wording**: `/v1/convert` and `/v1/merge` no longer claim PDF/A-3 compliance without verification.

### Removed
- **Serialize**: Removed phantom "Trial Mode" mention from `/v1/serialize` documentation.

## [1.6.9] - 2026-03-06

### Added

- **Validation**: `/v1/validate` responses now include `validation_completeness` (`full` / `partial`), `layers_executed`, and `layers_skipped` to explicitly surface which validation layers ran vs. were skipped (e.g. Saxon absent, VeraPDF unlicensed).

### Changed

- **Dependencies**: Bumped all Python packages to latest (fastapi 0.135.1, uvicorn 0.41.0, factur-x 3.15, lxml 6.0.2, etc.) and VeraPDF 1.26.5 → 1.28.2.

### Fixed

- **Documentation**: Corrected `/serialize` docstring — Community Mode returns HTTP 403, not obfuscated data.
- **Documentation**: Removed unconditional "Chorus Pro / KoSIT parity" claim from README; conditioned on `validation_completeness=full`.
- **Documentation**: Fixed `/v1/xml` section title (generates CII only, not CII/UBL).
- **Documentation**: Fixed typo "crypting" → "cryptic" in Smart Diagnostics section.

## [1.6.5] - 2026-03-03

### Added

- **Integration**: New Community Edition endpoint `POST /v1/merge` to embed external XML directly into PDF/A-3b files without going through JSON metadata. Ideal for ERP integrators injecting native ZUGFeRD/XRechnung payloads.
- **Documentation**: Overhauled integration recipes (Python, Node.JS, PHP) and updated the OpenAPI schema to include the new endpoint.

## [1.6.4] - 2026-03-02

### Changed

- **Licensing**: Simplified tier system from 4 tiers (`Evaluation`, `Business`, `Enterprise`, `OEM`) to 2 tiers (`Evaluation`, `Pro`) across all license-gated endpoints (`/v1/serialize`, VeraPDF validation).
- **Demo**: Upgraded Hugging Face demo to showcase Pro Engine endpoints and branding.

### Fixed

- **Hugging Face**: Backend subprocess now correctly inherits environment variables (including `LICENSE_KEY`) from the host process.

## [1.6.3] - 2026-02-27

### Fixed

- **Documentation**: Massive audit of `README.md` to perfectly align with code reality (removed ghost `/generate` references, added `/xml`, clarified validation rules, and added DevOps probes `/health`, `/diagnostics`, `/metrics`).
- **Licensing**: Added `OEM` tier support to the verification engine (`app/license.py`).
- **Deprecation**: Officially dropped "Batch processing" from the roadmap.

## [1.6.2] - 2026-02-25

### Added

- **Validation**: Introduced global (`VERAPDF_ENABLED`) and per-request (`validate_pdfa`) toggles for VeraPDF validation.

### Fixed

- **CI Pipeline**: Removed legacy `teaser_hidden_errors` assertions from unit tests that caused pipeline failures.

## [1.6.1] - 2026-02-24

### Changed

- **Serialization**: Replaced obfuscation-based "Community Mode" with a strict Pro feature Hard-Gate (HTTP 403) on `/v1/serialize` to streamline product tiers.
- **Documentation**: Overhauled READMEs to explicitly promote the "30-Day Evaluation" phase and added PDF/A-3 (VeraPDF) compliance to feature matrices.

### Removed

- **Codebase**: Deleted obsolete `app/services/trial_service.py` and 2 redundant integration test files (`trust_audit_validator.py`, `test_advanced_diagnostics.py`).
- **Schemas**: Cleaned up legacy `trial_notice` and `is_obfuscated` properties from API models and OpenAPI specification.

## [1.6.0] - 2026-02-23

### Added

- **Monetization**: Introduced Low-Touch "Evaluation Key" system (Ed25519 cryptography) unlocking 100% of Pro features for 30 days. Let the product sell itself.
- **API Standard**: All APIs now meticulously conform to RFC 9457 structured error format payloads.
- **Compliance**: Automatic SBOM (CycloneDX) deployment via Github Actions to anticipate the 2026 EU CRA constraints.

### Changed

- **Architecture Shift**: Hard-pivoted from native C-bindings (saxonche) to OS-level Subprocesses for VeraPDF and Saxon. Completely eradicates the silent JVM memory leaks and isolates MPLv2.0 dependencies.
- **Conversion Endpoints**: Deprecated the generic layout engine inside `/v1/convert` into a "Bring Your Own PDF" paradigm to achieve zero-maintenance.

## [1.5.5] - 2026-02-19

### Fixed

- **Metadata**: Synchronized system versioning and fixed metadata inconsistencies between `version.py`, `CITATION.cff`, and git tags.

## [1.5.4] - 2026-02-19

### Fixed

- **Validation**: Added missing `FACTUR-X_EXTENDED.xslt` resource to the engine.
- **Validator**: Fixed critical regression where `EXTENDED` profile was mismapping to strict rules. Validation is now correctly profile-aware.
- **Resources**: Restored missing `FACTUR-X_EXTENDED_codedb.xml` required by Saxon-C for the EXTENDED profile.

## [1.5.3] - 2026-02-19

### Added

- **Extraction**: Now extracts `due_date`, `registration_id` (SIRET), and `email` for both Seller and Buyer in CII and UBL formats.
- **Generator**: Added support for Buyer `registration_id` (SIRET) and `due_date` in Factur-X XML templates.

### Changed

- **Extraction**: Address fields are now flattened in JSON output (`line1`, `city`, etc.).
- **Cleanup**: Empty address fields (like `"..."`) are now sanitized and returned as `null`.

### Fixed

- **API**: Fixed critical 404 error on `/v1/serialize` endpoint by correctly including the router in `main.py`.
- **Serializer**: Resolved `AttributeError` in format detection when parsing CII/UBL files.
- **Reliability**: Refactored serialization tests to use `TestClient` for more robust validation of file uploads.

## [1.5.3] - 2026-02-19

### Fixed

- **Validator**: Fixed `SYS-SAXON` I/O error for `EXTENDED` profile by restoring missing `FACTUR-X_EXTENDED_codedb.xml` file.

## [1.5.2] - 2026-02-19

### Fixed

- **CI**: Fixed lint error (unused variable in tests).
- **Cleanup**: Removed accidental utility scripts from repository.

## [1.5.1] - 2026-02-19

### Changed

- **Validation Strictness**: The test suite now enforces strict compliance with current FNFE and XRechnung rules.
- **Corpus Cleanup**: Removed 105+ legacy test files (from external corpuses).
- **Reliability**: Eliminated the "Green Illusion" where invalid files were passing tests.

### Added

- **Demo**: Official Hugging Face Spaces integration (Hugging Face / Gradio UI).
- **Quality**: Global code cleanup and linting stabilization.

### Fixed

- **Validator**: (Critical) Fixed profile-aware validation bug (XSD/Schematron false negatives for MINIMUM/BASIC profiles).
- **CI**: Fixed release pipeline failures (Git checkout and linting).

### Fixed

- **CI**: Fixed release pipeline failure by converting `hf_space` to a regular directory (removed nested Git repository).

## [1.4.7] - 2026-02-18

### Fixed

- **Validator**: Fixed critical bug in `HybridValidationService` incorrectly applying EN 16931 business rules and XSD constraints to `MINIMUM`/`BASIC` profiles (False Negatives). Validation is now profile-aware.

## [1.4.6] - 2026-02-18

### Fixed

- **Integrity**: Corrected `uvicorn` entry point to support module execution (`python -m app.main`).
- **Robustness**: Hardened XPath helper in `ExtractionService` to correctly handle `_ElementUnicodeResult` from `lxml`.
- **Infrastructure**: Added `test` stage to Release pipeline and optimized Dockerfile (`PYTHONUNBUFFERED`).

## [1.4.5] - 2026-02-17

### Added

- **Tax Breakdown**: Real tax breakdown parsing from CII `ApplicableTradeTax` elements (category, rate, basis, amount per tax line) in both extractor and business serializer.
- **XRechnung PDF Support**: New `pdf_utils.py` wrapper with `pypdf` fallback for `xrechnung.xml` attachments not recognized by upstream `facturx` library.
- **Tests**: Added `/health` endpoint test, `/v1/xml` endpoint tests, invalid corpus files (malformed, truncated, non-invoice XML). Wired full ZUGFeRD 2.4 + XRechnung 3.0.2 corpus (181 tests).

### Changed

- **Async Endpoints**: All 5 API endpoints converted from `def` to `async def` for better throughput under load.
- **Dependencies**: Removed unused `setuptools` and `jaraco.context` from `requirements.txt`.

### Removed

- **Dead Code**: Removed unused `get_trial_file_info()` from `trial_service.py`.

## [1.4.4] - 2026-02-17

### Added

- **CI Pipeline**: Full CI workflow with Ruff linting, pytest, and Docker build verification on all branches and PRs.
- **Ruff Configuration**: Added `pyproject.toml` with project-wide linting rules and per-file ignores.

### Fixed

- **Security**: Fixed XXE vulnerability in Smart Diagnostics engine (Jules PR).
- **Performance**: Optimized `HybridValidator` process pool and metrics collector locking (Jules PRs).
- **Stability**: Fixed unsafe list access in `BusinessSerializer` (Jules PR).
- **Code Quality**: Added type hints to extractor service, refactored brittle path handling (Jules PRs).
- **Testing**: Added XML endpoint tests, license logic tests, Smart Diagnostics proactive scan tests, validator error humanization tests (Jules PRs).
- **Diagnostics**: Fixed `facturx` version attribute access using safe `getattr` pattern.

### Changed

- **Branch Hygiene**: Consolidated all `release/v1.4.4` changes into `main`. Cleaned up 19 stale branches.

## [1.4.3] - 2026-02-10

### Added

- **CI Strengthening**: Integrated `Ruff` for strict linting and static analysis in the CI pipeline.
- **Docker Build Verification**: Added automated steps to build and verify the Docker image stability.

### Fixed

- **Code Quality Overhaul**: Resolved over 20 critical linting errors including bare except statements, unused variables, and import issues.
- **Test Corpus Integrity**: Corrected the classification of test files (moved valid files mistakenly placed in `invalid/`).
- **Import Handling**: Fixed `PRODUCT_VERSION` import errors by correctly referencing `app.version.__version__`.
- **Trial Mode Reliability**: Verified and confirmed that Trial Mode is robust to file organization changes (content-hash based).

## [1.4.2] - 2026-02-10

### Fixed

- **BOM Management**: Added `utf-8-sig` decoding in `HybridValidator` to support official FNFE/Factur-X 1.08 examples containing a UTF-8 Byte Order Mark.
- **API Robustness**: Aligned conversion and extraction metadata with strict EN 16931 rules (added mandatory payment terms/due dates).

### Changed

- **Internal Harmonization**: Centralized version metadata in `app/version.py` (Single Source of Truth).
- **Quality Gate**: Hardened the generator's internal validation to catch compliance errors before PDF delivery.

## [1.4.1] - 2026-02-09

### Changed

- **Harmonized Versioning**: Unified version to 1.4.1 across all assets.
- **Startup Integrity**: Implementation of a "Fail Fast" check for critical XSD schemas.
- **Documentation**: Added strategic "Architecture Decisions" section and v2.0 Roadmap.

## [1.4.0] - 2026-02-08

### Added - **Angles Morts** & Resilience Edition

#### Advanced Diagnostics (Pro)

- **Prophylactic Rules ("Angles Morts")**:
  - `BR-CO-09-EXT`: Cross-check between Seller Country and VAT Intra prefix (e.g. FR vs DE).
  - `BT-3-CONTEXT`: Detection of "Auto-Avoir" (Negative Total with Invoice Type 380).
  - `BT-1-FORMAT`: Validation of Invoice Number characters to prevent rejection by Chorus Pro.
- **Financial Resilience**:
  - Added `ROUNDING_TOLERANCE` (0.05€) for tax calculation rules (BR-CO-10, 13, 14).
  - Technical rounding errors are now downgraded to Warnings instead of blocking Errors.

#### Fixed

- **FastAPI Schema**: Fixed a critical bug where Pro diagnostics were silently stripped from the API response (`response_model` Union fix).
- **Trial Mode**: Fixed regression in Community mode tests when a trial file was present.
- **Validation Infrastructure**: Fixed XSD validation failures on Windows due to path length limitations by relocating and shortening schema filenames.
- **XML Generation**: Fixed Schematron rule `PEPPOL-EN16931-R008` (empty elements) by ensuring mandatory delivery fields always have content (fallback to invoice date).
- **Localization**: Standardized diagnostic titles and explanations to English to ensure consistency across all deployments and test stability.
- **Multiprocessing**: Fixed "spawn" bootstrapping errors on Windows for the validation process pool.

## [1.3.3] - 2026-01-30

### Added

- **New Endpoint `POST /v1/xml`**: Directly generate Factur-X/CII XML without a PDF wrapper.
- **Extended Field Coverage**: Added `id` and `global_id` support for `ShipToParty` and `BuyerTradeParty` to satisfy Issue #5 requirements.
- **XRechnung Compliance**: Better mapping for `Leitweg-ID` using `BuyerReference`.
- **Enhanced Metrics**: Split business vs operational metrics on `/metrics` (Pro feature).
- **Diagnostics**: Added Git hash and build date to `/diagnostics`.

## [1.3.2] - 2026-01-27

### Changed

- Minor stabilization and security patches for production readiness.

## [1.3.1] - 2026-01-26

### Added - Security & Compliance Edition

#### Core Features

- **Audit Alignment**: Harmonized ZUGFeRD 2.4 claims across `main.py`, README, and Docker Hub for strict compliance.
- **GEO (Generative Engine Optimization)**: Enhanced documentation with "Standards Compatibility Matrix" and structured metadata for AI indexing.
- **Security Governance**: Added explicit vulnerability policy (`SECURITY.md`) and manual "Air-Gap" verification steps.
- **Resilient Profile Detection**: Added fallback logic for newer XRechnung/Factur-X URNs to improve parsing robustness.

#### Documentation

- **Pillar Content**: Added dedicated tutorials for Node.js integration and Schematron validation (`docs/tutorials/`).
- **Social Proof**: Added explicit platform badges (amd64/arm64) and compliance signals.

## [1.0.0] - 2026-01-13

### Added - Initial Production Release

#### Core Features

- **POST /v1/convert** - Convert PDF + JSON metadata to Factur-X PDF (PDF/A-3)
- **POST /v1/validate** - Validate Factur-X/ZUGFeRD PDFs and XML against EN 16931
- **POST /v1/extract** - 🆕 Extract XML from Factur-X PDF and return structured JSON (wedge prioritaire 2026)
- **GET /diagnostics** - Comprehensive system diagnostics for support
- **GET /health** - Health check endpoint
- **GET /healthz** - Alternative health endpoint (Kubernetes-style)

#### Self-Hosted "Appliance" Features

- 1 Docker Compose deployment with resource limits
- ✅ Environment-based configuration (.env)
- ✅ Health checks and automatic restart
- ✅ JSON logging for observability
- ✅ Support bundle generation tool
- ✅ Air-gapped operation (no Internet required)

#### Documentation

- `README_SELF_HOSTED.md` - 5-minute quickstart
- `RUNBOOK.md` - Operations and troubleshooting guide
- `UPGRADE.md` - Upgrade and rollback procedures
- `SUPPORT_POLICY.md` - Strict support policy (N and N-1 only)
- `LICENSING.md` - Community vs Paid edition details
- `BUILD.md` - Build and deployment instructions

#### Diagnostics & Observability

- Version tracking (SemVer)
- Git hash and build date tracking
- Dependency version reporting
- Runtime configuration visibility
- Memory usage monitoring
- Feature flags detection
- Licensing mode detection (community/paid)

#### Testing

- 10+ integration tests covering all endpoints
- End-to-end workflow test (convert → validate → extract)
- Non-Factur-X PDF detection test
- Diagnostics endpoint test

#### Compliance

- EN 16931 validation (all profiles)
- PDF/A-3 output with AFRelationship metadata
- ZUGFeRD 2.2 / Factur-X 1.0 compatible

### Technical Details

- **Python**: 3.11+
- **Framework**: FastAPI
- **Core Library**: akretion/factur-x 3.15
- **Validation**: xmlschema
- **Template Engine**: Jinja2 for XML generation
- **Container**: Docker (Python 3.11-slim)
- **Deployment**: Docker Compose

### Security

- No data persistence (fully stateless)
- No telemetry or "phone home"
- Privacy-first: PDFs/invoices never logged
- Air-gapped operation supported

### Support

- Community edition: Full features, community support
- Paid edition: Commercial support with SLA
- Support policy: N and N-1 versions only

---

## [1.6.8] - 2026-03-06

### Added

- **Compliance — France 2026**: Embedded official FNFE/DGFIP **BR-FR CTC v1.2.0** Schematron rules (CII + UBL). `HybridValidationService` now auto-detects `CountryID=FR` and applies French mandate rules on top of EN 16931 — achieving true **Chorus Pro parity**.
- **Compliance — Germany (XRechnung UBL)**: Integrated the official **KoSIT XRechnung-UBL-validation.xsl** (xrechnung-3.0.2-schematron-2.5.0). XRechnung invoices in UBL format now run against German BR-DE rules instead of the generic EN 16931 base.
- **Schema Coverage**: Added **Factur-X 1.08 BASICWL XSD** (+ 3 dependency schemas) for structural validation of the BASICWL profile.
- **Extraction — UBL CreditNote**: Full extraction support for `<CreditNote>` root element (UBL 2.1): `CreditNoteLine`, `CreditedQuantity`, `billing_reference`, `tax_point_date`, and `document_type` ("invoice" | "credit_note") exposed in `/v1/extract`.
- **Validation — EN16931 UBL**: Updated EN 16931 UBL Schematron to **CEN v1.3.15**.

### Changed

- **XRechnung 2.3 deprecated**: Profile is now explicitly rejected (HTTP 422) with a clear upgrade message pointing to 3.0.x. Silent fallback has been removed.

## [1.6.7] - 2026-03-05

### Added

- **Smart Diagnostics (Pro)**: Added Proactive Scan rules `INVALID-IBAN`, `TOO-MANY-DECIMALS`, `INVALID-DATE`, `INVALID-COUNTRY-CODE` natively.
- **Diagnostics Context**: Anomalous values (like incorrect IDs or amounts) are now strictly mapped into the `Diagnostic.context` payload.
- **DevOps**: Split Docker health checks into `/health` (liveness) and `/healthz` (deep readiness) with optimized `requirements-dev.txt`.

### Changed

- **Validation Robustness**: Fixed the diagnosis parsing engine directly accessing PDF-wrapped `xml_content`.
- **Proactive Severity**: Downgraded Proactive Scan severity from `error` to `warning` to better align with its "Pre-Clearance Audit" purpose.

## [1.6.6] - 2026-03-03

### Changed

- **Massive Architectural Refactoring** (`#merge-lucid-hoover`): Centralised validation helpers, extracted boilerplate, and improved DRY compliance across `app/api.py`.
- **Modern FastAPI Lifespan**: Migrated from `@on_event("startup")` to `@asynccontextmanager lifespan` for elegant lifecycle handling and graceful shutdowns.
- **Improved Security Posture**: Moved development tools (`pytest`, `httpx`) out of the production Docker image via `requirements-dev.txt`.
- Added global HTTP header `X-Content-Type-Options: nosniff` on all responses to pass rigorous automated security audits.

### Added

- **Industrial Observability**: Added `RequestIdMiddleware` to inject a `x-request-id` into every API context and propagate it through JSON structured logs and response headers.
- **Isolated Metrics Router**: Refactored Prometheus `/metrics` endpoint into its own `app/observability.py`.
- Smart warning at engine startup if PRO metrics are enabled without an authentication token (`METRICS_TOKEN`).
- Detailed `docker-compose.yml` example provided at the repository root to simplify testing and PLG onboarding.
- Enforced automated CI coverage thresholds (`pytest --cov-fail-under=60`).

### Planned for 1.1.0

- Enhanced extraction for EN 16931 and Extended profiles
- Line items extraction for all profiles
- Batch conversion API (❌ dropped)
- Async processing for large PDFs

### Planned for 2.0.0

- Advanced profiles support (extended features)
- Attachment handling
- Digital signature verification
- Web UI for manual testing

---

[1.0.0]: https://github.com/yourorg/facturx-api/releases/tag/v1.0.0
