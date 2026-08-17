# Cyber Resilience Act note

Factur-X Engine does not claim certification or conformity with the EU Cyber
Resilience Act. This page is not a declaration of conformity and is not legal
advice.

The repository currently provides implementation evidence that operators may
use in their own assessment:

- a non-root runtime user in the official Dockerfile;
- optional execution with restricted networking;
- dependency and container scanning workflows;
- release SBOM generation when the release workflow runs;
- a private vulnerability-reporting process described in `SECURITY.md`.

No release frequency, vulnerability acknowledgement time, remediation deadline,
support obligation, or security outcome is promised. Deployment configuration,
network exposure, access control, update policy, logging, backups, and the final
regulatory assessment remain the operator's responsibility.
