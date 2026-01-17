# 🚀 Next Steps (Post-Launch)

## 🟢 Phase 1: Immediate Post-Launch (Days 1-3)

- [ ] **External Verification**
  - [ ] Ask a friend/colleague to `docker run` the image from a virgin machine.
  - [ ] Verify Lemon Squeezy checkout flow (up to payment).
- [ ] **Marketing Kick-off**
  - [ ] Update LinkedIn Profile (Project Section).
  - [ ] Post on specific subreddits (r/selfhosted, r/python, r/accounting_software).
  - [ ] **Docker Hub Description**: Double-check the manually copied description matches README.

## 🟡 Phase 2: Operations & Sales (Weeks 1-2)

- [ ] **Content Marketing** (Drive Traffic)
  - [ ] Write "How to generate Factur-X in Python" blog post (linking to repo).
  - [ ] Create a "1-minute stress test" video.
- [ ] **Sales Monitoring**
  - [ ] Monitor "Try" vs "Buy" conversion on Lemon Squeezy.
  - [ ] Check ProtonMail for first enterprise inquiries.

## 🔵 Phase 3: Product Evolution (Month 1+)

- [ ] **Feedback Loop**
  - [ ] Review GitHub Issues (if any).
  - [ ] Check Docker Hub "Pulls" statistics.
- [ ] **Features (v1.1.0)**
  - [ ] *Idea*: Support more input formats (JPEG scan to Factur-X)?
  - [ ] *Idea*: Webhook support for async processing?
  - [ ] **Connectors Strategy**: Explore creating a specific **n8n Community Node**.
    - Why n8n? It targets "Self-Hosted" users (perfect match).
    - Why not Zapier? Zapier requires a public Cloud API (Salesforce model), incompatible with our "Private/Offline" promise.

---

## ✅ Completed Milestones

- [x] **v1.0.0 Release** (2026-01-17)
- [x] **Security Audit & Hardening** (Git Nuke)
- [x] **Automated CI/CD** (GitHub Actions -> Docker Hub)
- [x] **Commercial Setup** (Lemon Squeezy + Pro License Keygen)
- [x] **Examples & Docs Polish** (Added `examples/` folder and clarified Wording)
- [x] **Odoo Integration (v1.0.0 Proof of Concept)** (2026-01-17)
  - [x] Working `/v1/extract` connection.
  - [x] Automatic account discovery and summary line fallback.
  - [x] Date format normalization.
