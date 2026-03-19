# Security Policy

## Supported Versions

| Version | Supported |
|---------|-----------|
| latest  | Yes       |
| < latest | Critical fixes only for 12 months |

## Reporting a Vulnerability

If you discover a security vulnerability in Factur-X Engine, please report it responsibly.

**Do NOT open a public GitHub issue for security vulnerabilities.**

### How to Report

1. **Email**: Send details to **security@nexaflow.io**
2. **Include**: Affected version, reproduction steps, potential impact
3. **Response time**: We acknowledge within **48 hours** and provide an initial assessment within **5 business days**
4. **Fix SLA**:
   - CVSS >= 9.0 (Critical): Patch within **72 hours**
   - CVSS 7.0-8.9 (High): Patch within **7 days**
   - CVSS 4.0-6.9 (Medium): Next scheduled release

### What to Expect

- We will confirm receipt of your report within 48 hours
- We will keep you informed of progress toward a fix
- We will credit you in the release notes (unless you prefer anonymity)
- We will NOT take legal action against researchers who follow responsible disclosure

## Security Practices

- **Air-gapped by design**: No outbound network calls, no telemetry, no phone-home
- **SBOM**: Generated on every release (CycloneDX format)
- **Dependency scanning**: Daily Trivy scans on Docker image
- **Supply chain**: SHA-256 verification for VeraPDF and Saxon-HE JARs
- **Non-root container**: Application runs as unprivileged `appuser`
- **CRA compliance**: See [CRA_COMPLIANCE.md](./docs/cra.md)

## Scope

This policy applies to the `facturx-engine/facturx-engine` repository and the official Docker image `facturxengine/facturx-engine`.
