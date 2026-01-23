# Pricing Strategy (2026) - DRAFT

**Philosophy**: Shift from "User Counting" (impossible in Black Box) to "Developer Capacity" (verifiable).

## 1. Pro License (Standard)

* **Target**: SME / Internal Dev Teams.
* **Price**: **499€ / year**.
* **Usage**: Internal Use Only.
* **Scope**: 1 Production Site (Dev/Staging included).

## 2. OEM / Redistribution Licenses

* **Target**: ISVs, ERP Vendors, SaaS.
* **Logic**: Tiered by size of the integrating technical team (Proxy for company size & value).

| Tier | Price / Year | Cap | Target Profile |
| :--- | :---: | :--- | :--- |
| **OEM Starter** | **~2 490 €** | 1 Developer | Niche SaaS / Freelance integration. |
| **OEM Growth** | **~5 990 €** | Team < 5 Devs | Established SME ERP. |
| **OEM Scale** | **Custom / ~14k€** | Unlimited | Major Players. Includes Legal Indemnification using Escrow. |

## 3. Demo Strategy (Converting Free to Paid)

* **Problem**: "Free" users can't validate if the parser works because of `***` masking.
* **Solution**: "Smart Demo".
  * **Structure**: Real (Lines, Quantities are correct).
  * **Values**: Faked (Prices = 100.00, Totals = Math(Qty * 100)).
  * **Result**: Devs can prove "it works" technically, but Finance can't use it.

## 4. Perpetual Fallback

* If subscription ends, the Docker container **keeps running forever**.
* Access to **Updates** (Security/Tax Compliance) stops.
* Watermark "Unmaintained Version" appears on generated PDFs after grace period (Future Feature).
