# 📅 Project History Log

## 2026-01-17: 🔌 Odoo Integration & Import Robustness

* **Milestone**: Successfully integrated **Factur-X Engine** with **Odoo 16.0**.
* **Fixes**:
  * **Date Parsing**: Resolved crash by converting Factur-X XML dates (`YYYYMMDD`) to Odoo dates (`YYYY-MM-DD`).
  * **Summary Lines**: Implemented fallback for "Minimum" profile invoices (Summary line created with full amount).
  * **Accounting**: Added automatic discovery of default expense accounts to ensure line validity.
  * **Bugfix**: Corrected API response traversal (accessing `invoice_json` nested object).
* **Verification**: Full end-to-end import confirmed (Vendor, Date, Reference, and Amount 1234.56 € all present).

## 2026-01-17: 🚀 v1.0.0 Public Launch & Security Hardening

* **Milestone**: Released **Factur-X Engine Community Edition v1.0.0**.
* **Distribution**:
  * **Docker Hub**: `facturxengine/facturx-engine` (Automated Build via GitHub Actions).
  * **GitHub**: `facturx-engine/facturx-engine` (Source Code - Community Edition).
* **Commercial**:
  * Sales page live on Lemon Squeezy.
  * Email `facturx.engine@protonmail.com` configured.
* **🚨 Security Incident & Resolution**:
  * *Issue*: Initial Git verification revealed accidental commit of `private_key.hex`, `admin_keygen.py` and `*_pro.py` in previous local history.
  * *Fix*: **Full Git History Nuke**. Repository reset to a single "Initial Commit" containing *only* the whitelist-safe Community code.
  * *Prevention*: Implemented aggressive **Whitelist-based .gitignore** (ignoring all `*.md`, `*.py` by default, except essential files).
  * *Status*: GitHub repository is now essentially clean and secure.

## 2026-01-13: 📦 Productization Sprint Completed

* **Deliverables**:
  * New `/v1/extract` endpoint (wedge feature).
  * Diagnostics & Support Bundle system.
  * Self-Hosted Deployment Pack (`deploy/selfhosted`).
  * Support Policy (N/N-1).

## 2025-12-XX: MVP Development

* Initial development of Factur-X generation engine.
* PDF/A-3 compliance and XML embedding logic.
