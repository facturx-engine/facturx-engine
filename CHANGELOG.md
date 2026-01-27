# Changelog - Factur-X API

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
