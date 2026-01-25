# Factur-X Engine - Cyber Resilience Act (CRA) Compliance Statement

**Version:** 1.0
**Date:** 2026-01-19
**Scope:** Factur-X Engine (Pro & Community)

## Preamble

This document outlines how **Factur-X Engine** adheres to the principles of the **EU Cyber Resilience Act (CRA)**. Our compliance strategy is based on simplicity, minimalism, and "Security by Design".

---

## 1. Security by Design

We do not rely on complex active defenses. Instead, we rely on **architectural invariants** that reduce the attack surface to near zero.

### 1.1 "Offline First" Architecture

* **Reality:** The container is designed to run without *any* outbound internet connection.
* **Compliance Benefit:** Data exfiltration vectors are structurally impossible if the host network is configured correctly.
* **Verification:** `docker run --network none ...` functions perfectly for all core features.

### 1.2 "Read-Only" Execution

* **Reality:** The application does not write to its own code, configuration, or system directories at runtime.
* **Compliance Benefit:** Persistence of malware or unauthorized modifications is prevented.
* **Verification:** The container can be run with `--read-only` (with `/tmp` mounted as tmpfs).

### 1.3 "Fail-Fast" Integrity Checks

* **Reality:** The engine validates its own integrity (License & Build Date) at startup.
* **Compliance Benefit:** If critical components or the system clock are tampered with, the service refuses to start, preventing undefined or insecure states.

---

## 2. Vulnerability Management

We commit to a transparent and reactive vulnerability management process.

### 2.1 Software Bill of Materials (SBOM)

* **Commitment:** Every release includes a machine-readable SBOM (`sbom.json`) listing all Python dependencies and system libraries.
* **Goal:** Enable users to instantly verify if a newly discovered CVE affects their instance.

### 2.2 Update Policy

* **Frequency:** We rebuild our Docker images monthly to pull the latest security patches from the base OS (Debian/Alpine) and Python runtime.
* **SLA:** Critical vulnerabilities (CVSS > 9.0) affecting the engine's dependencies trigger an immediate hotfix release within 72 hours.

---

## 3. Data Sovereignty & GDPR

While not strictly CRA, data sovereignty is a key component of our trust framework.

* **No Telemetry:** The engine contains zero analytics, tracking, or "phone home" mechanisms.
* **Ephemeral Processing:** Invoice data is processed in memory and discarded immediately after the API response. No data is persisted on disk.

---

## 4. Limitation of Liability & Disclaimer

**IMPORTANT NOTICE:**

1. **"As Is" Basis**: Factur-X Engine is provided "as is". While we strictly adhere to the processes described in this document, we cannot guarantee immunity against all cyber threats.
2. **Shared Responsibility**: The final security posture relies heavily on the **Integrator's environment**. We certify the container's integrity, but we are not responsible for:
    * Insecure host configurations (e.g., exposing the API to the public internet).
    * Compromised private keys managed by the user.
    * Outdated versions (failure to apply updates).
3. **Liability Cap**: As stated in our EULA, our liability is strictly limited to the amount paid for the software license. We are not liable for any indirect damages, data loss, or business interruption resulting from a security incident.
