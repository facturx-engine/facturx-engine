# Changelog - Factur-X API

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

## [Unreleased]

### Planned for 1.1.0

- Enhanced extraction for EN 16931 and Extended profiles
- Line items extraction for all profiles
- Batch conversion API
- Async processing for large PDFs

### Planned for 2.0.0

- Advanced profiles support (extended features)
- Attachment handling
- Digital signature verification
- Web UI for manual testing

---

[1.0.0]: https://github.com/yourorg/facturx-api/releases/tag/v1.0.0
