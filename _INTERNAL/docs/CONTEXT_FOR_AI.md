# 🛑 CRITICAL CONTEXT FOR AI ASSISTANT 🛑

**READ THIS BEFORE MODIFYING ANYTHING.**

This project (**Factur-X Engine**) has transitioned to a **Single Image / Open-Core architecture**. Security is now managed via Private Repository Injection and Runtime License Enforcement.

---

## 🔐 1. Security Invariants (DO NOT TOUCH)

1. **PRO Source Protection (Private Repo).** (🚨 CRITICAL AI RULE 🚨)
    * Proprietary code (specifically the Full Extractor logic) is stored in a **Private Repository** (`facturx-engine-pro-source`).
    * **NEVER** copy-paste full code from `facturx-engine-pro-source/extractor.py` into the public repository's `app/services/extractor.py`.
    * Public `app/services/extractor.py` **MUST** remain the "Demo Version" (masking amounts, adding watermarks).

2. **Automated "Pro" Infiltration (CI/CD ONLY).**
    * The "Full" version is created during the GitHub Actions build (`publish-release.yml`).
    * It uses an SSH Deploy Key (`PRO_REPO_KEY`) to fetch the private source and overwrite the demo stub *just before* the Docker build.
    * **NEVER** expose the `PRO_REPO_KEY` or the private repo URL in public files.

3. **`private_key.hex` & `admin_keygen.py`.**
    * These files reside **ONLY** in the private repository.
    * **NEVER** bring them back to the public repository.
    * They are the "Keys to the Kingdom" used to generate commercial license keys.

4. **"Fail Fast" License Enforcement.**
    * If `LICENSE_KEY` is provided but invalid (tampered or wrong signature) -> The application **MUST CRASH** at startup (`sys.exit(1)`).
    * This prevents accidental fallback to Demo Mode for paying customers.

---

## 🏗️ 2. Architecture Overview: Single Image Model

* **Distribution**: ONE public image on Docker Hub (`facturxengine/facturx-engine`).
* **Modes**:
  * **Community/Demo**: Default mode. Full Generation/Validation.
    * **Extraction**: "Smart Demo" mode (`app/services/extractor.py`).
      * **Behavior**: Extracts REAL structure (correct line counts, quantities) but FAKES financial values (Prices fixed to 100.00, Totals recalculated).
      * **Goal**: Allows technical validation of the parser without enabling free commercial use.
  * **Pro**: Full access. Unlocked by setting `-e LICENSE_KEY=...`.
* **Build Process**: Unified Multi-stage Dockerfile. Stage `builder-pro` compiles the Cython modules (IP protection) and wipes source files.

---

## 📝 3. Current State (v1.2.0 - Single Image Release)

* **Version**: v1.2.0 (2026-01-21)
* **Architecture**: ✅ **Architectural Unified Single Image**
* **Security**: ✅ **Private Repo Injection via SSH Agent**
* **Licensing**: ✅ **Ed25519 Cryptographic Keys (Self-Hosted/Offline)**
* **Concierge Workflow**: Keys are generated manually offline (`tools/keygen.ps1`) to ensure private keys never touch the internet. Emails frame this delay as a "Security Feature".
* **Distribution**:
  * **Registry**: **Scarf Gateway** (`facturxengine.docker.scarf.sh`).
  * **Reason**: Provides telemetry on "Air-gapped" pulls without compromising user privacy.
  * **Invariant**: Documentation MUST always point to the Scarf URL, not Docker Hub directly.

---

## 🚀 4. Release & Deployment Procedures

### Production Release (Automated)

* **Trigger**: Push or Tag on `main` branch.
* **Actions**: GitHub Actions (`.github/workflows/publish-release.yml`).
* **Steps**:
    1. Sets up SSH for `facturx-engine-pro-source`.
    2. Overwrites `app/services/extractor.py` (Demo) with the Pro version.
    3. Builds Docker image with `BUILD_DATE` injection.
    4. Pushes to Docker Hub (via Scarf Gateway for tracking).

### Security & Compliance (CRA)

* **Dependency Pinning**: All dependencies in `requirements.txt` MUST be strictly pinned (e.g., `jaraco.context==6.1.0`) to avoid upstream supply chain attacks or vulnerability regressions in CI.
* **Trivy Scan**: The pipeline `security.yml` enforces a "Fail Fast" policy on High/Critical CVEs.

---

## 💼 5. Business Configuration

* **Sales Channel**: Lemon Squeezy (Selling **License Keys**, not software files).
* **Support**: `facturx.engine@protonmail.com`.
* **Perpetual Fallback**: Users own the version they bought. If maintenance expires, they can continue using their current version (Validation logic is version-aware via `BUILD_DATE`).

---

## 🎭 6. Persona & Strategy

**Role:** CTO & Product Strategist.
**Goal:** High-Sovereignty B2B SaaS (GDPR, CRA, Offline).

1. **Protect the IP**: Everything valuable is Cythonized and kept in the private repo.
2. **Support the User**: User is a solo founder. Automate everything (Test, Build, Deploy).
3. **Validate Reality**: Always test with the *real* image from Docker Hub to ensure local/CI parity.

---

*This file was updated on 2026-01-23 to reflect the migration to the secure Single Image architecture.*
