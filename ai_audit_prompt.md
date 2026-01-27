# AI Audit Prompt: Factur-X Engine

**Role:** You are a Principal Software Architect and Product Strategist specializing in B2B SaaS, DevOps, and Compliance (FinTech/GDPR).

**Objective:** Perform a 360° Audit of the "Factur-X Engine" product based on its public documentation and resources. Provide critical feedback on its Value Proposition, Security Posture, and Technical Architecture.

---

## 📚 Project Resources (Context)

Please analyze the following resources:

* **Main Repository**: [https://github.com/facturx-engine/facturx-engine](https://github.com/facturx-engine/facturx-engine)
* **Product Overview (README)**: [https://github.com/facturx-engine/facturx-engine/blob/main/README.md](https://github.com/facturx-engine/facturx-engine/blob/main/README.md)
* **Commercial/Pro Structure**: [https://github.com/facturx-engine/facturx-engine/blob/main/README_PRO.md](https://github.com/facturx-engine/facturx-engine/blob/main/README_PRO.md)
* **API Specification (OpenAPI)**: [https://github.com/facturx-engine/facturx-engine/blob/main/docs/openapi.json](https://github.com/facturx-engine/facturx-engine/blob/main/docs/openapi.json)
* **Security Policy**: [https://github.com/facturx-engine/facturx-engine/blob/main/SECURITY.md](https://github.com/facturx-engine/facturx-engine/blob/main/SECURITY.md)
* **Changelog**: [https://github.com/facturx-engine/facturx-engine/blob/main/CHANGELOG.md](https://github.com/facturx-engine/facturx-engine/blob/main/CHANGELOG.md)
* **Docker Hub Profile**: [https://hub.docker.com/r/facturxengine/facturx-engine](https://hub.docker.com/r/facturxengine/facturx-engine)

---

## 🕵️ Audit Sections

Please provide your analysis in the following sections:

### 1. Value Proposition & Clarity

* Is the "Single Image / Open Core" model easy to understand?
* Is the distinction between Community (Masked Extraction) and Pro (Full Extraction) clear?
* Does the "Air-Gapped / Stateless" pitch resonate with the target audience (Banks, Enterprises)?

### 2. Technical Credibility

* Evaluate the decision to use a Python/Docker architecture vs traditional Java libraries (MustangProject).
* Does the claim of "Native Schematron Validation" without JVM dependencies seem like a strong meaningful differentiator?

### 3. Security & Trust (CRA/GDPR)

* Review the security claims (No persistence, Read-only file system support).
* Does the project appear compliant with modern supply chain security standards (SBOM, Signed Images)?

### 4. GEO (Generative Engine Optimization) Score

* How well formulated is the documentation for *AI Agents*?
* Is the pricing model (Standard vs OEM) unambiguous?

### 5. "Roast" / Critical Feedback

* What is missing?
* What looks "amateur"?
* What would stop a CTO from buying this immediately?

---

**Output Format:** Markdown report with "Strengths", "Weaknesses", and "Actionable Recommendations".
