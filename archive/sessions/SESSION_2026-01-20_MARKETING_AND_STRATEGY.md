# Session Log: 2026-01-20 (Marketing & Strategy)

**Goal:** Accelerate Acquisition and Define Trust Strategy.

## ✅ Key Achievements

### 1. Unified Trust Strategy (The "Trust Pack")

* **Synced:** `README.md` (GitHub), `DOCKER_HUB_README.md`, and `README_COMMUNITY.md` are now aligned.
* **Asset:** `CRA_COMPLIANCE.md` is central to the sales pitch.
* **Badges:** Added "CRA Compliant", "Offline", "GDPR" badges to Docker Hub to convert traffic.

### 2. Acquisition Funnel Optimization

* **"Demo Mode" Teaser:** Explicitly added the `curl ... /extract` command in the Community/Docker docs to let users "Try before they buy".
* **Traffic Analysis:** Confirmed that high Docker pulls (~750) are mostly bots, validating the need for stronger Human engagement levers (Pyodide).

### 3. SEO Launch ("Error-Code Marketing")

* **Tactic:** Using GitHub as a Blog.
* **Content:** Published first article [`docs/troubleshooting/BR-CO-09_seller_vat_id_missing.md`](../../docs/troubleshooting/BR-CO-09_seller_vat_id_missing.md).

### 4. Strategic Decisions

* **Licensing:** Validated the **"Maintenance Window" model** (JetBrains style) vs "Hard Expiry".
  * *Logic:* `RELEASE_DATE < MAINTENANCE_UNTIL`.
  * *Benefit:* Solves the "Perpetual Fallback" legal requirement without manual key generation.
* **Pivot:** Documented **"InvoiceSeal"** as a future vertical pivot for ISVs (Campings, Dentists ERPs) in Phase 2.

### 5. R&D Initiated

* **Pyodide (Web Validator):** Feasibility plan created (`_INTERNAL/docs/PYODIDE_POC_PLAN.md`).
  * *Next Step:* Build `tests/pyodide_poc/index.html` to test `lxml` in WASM.

## 📝 Next Steps (Tech Focus)

1. **Execute Pyodide POC**: Verify `lxml` in browser.
2. **Refactor License Logic**: Implement the `maintenance_until` check in `app/license.py`.
