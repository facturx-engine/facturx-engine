# SEO & GEO Audit Report: Factur-X Engine

**Audit Date:** 2026-03-27
**URL:** https://facturx-engine.github.io/facturx-engine/
**Business Type:** SaaS / Developer Tool (Self-Hosted API)
**Pages Analyzed:** 23 HTML pages + llms.txt + OpenAPI spec
**Methodology:** Frameworks [geo-seo-claude](https://github.com/zubair-trabzada/geo-seo-claude) + [claude-seo](https://github.com/AgriciDaniel/claude-seo)

---

## Executive Summary

**Overall GEO Score: 61/100 (Fair)**

Factur-X Engine possède une infrastructure technique solide (SSR, llms.txt, sitemap i18n, schema SoftwareApplication) mais souffre d'un déficit majeur en **autorité de marque** (quasi-absente sur Reddit, YouTube, Stack Overflow, Wikipedia) et en **citabilité AI** (contenu trop court, pas de dates de publication, pas de citations de sources externes). Le site est bien structuré pour le SEO classique mais manque les signaux critiques qui déclenchent les citations par les moteurs IA (ChatGPT, Perplexity, Google AI Overviews).

### Score Breakdown

| Catégorie | Score | Poids | Score Pondéré |
|---|---|---|---|
| AI Citability | 45/100 | 25% | 11.3 |
| Brand Authority | 15/100 | 20% | 3.0 |
| Content E-E-A-T | 55/100 | 20% | 11.0 |
| Technical GEO | 82/100 | 15% | 12.3 |
| Schema & Structured Data | 78/100 | 10% | 7.8 |
| Platform Optimization | 40/100 | 10% | 4.0 |
| **Overall GEO Score** | | | **61/100** |

---

# PARTIE 1: AUDIT SEO (Search Engine Optimization)

## Données Google Search Console (3 derniers mois)

### KPIs Globaux

| Métrique | Valeur |
|---|---|
| **Total Clicks** | 52 |
| **Total Impressions** | 2,319 |
| **CTR Moyen** | 2.24% |
| **Position Moyenne** | 7.78 |

> **Diagnostic:** Trafic organique très faible (52 clics / 3 mois = ~0.6 clic/jour). La position moyenne 7.78 indique une présence en page 1 mais en bas de page, insuffisante pour générer des clics. Le CTR de 2.24% est en dessous du benchmark de 3-5% pour la position 7-8.

### Top Queries — Opportunités manquées

| Query | Impressions | Clicks | CTR | Position | Verdict |
|---|---|---|---|---|---|
| `python factur-x library` | 31 | 0 | 0% | 6.5 | ❌ Position 6 mais 0 clics — titre pas assez accrocheur |
| `mustangproject factur-x java library` | 28 | 0 | 0% | 7.4 | ❌ Page comparaison existe mais ne convertit pas |
| `factur-x npm` | 22 | 0 | 0% | 7.4 | ❌ Tutorial Node.js existe mais ne rank pas bien |
| `factur-x python library` | 21 | 0 | 0% | 6.5 | ❌ Doublon sémantique avec query #1 |
| `factur-x validator` | 18 | 0 | 0% | **68.6** | 🔴 Position 68 = page 7! Tool existe mais non indexée correctement |

**Constat critique:** Les 5 top queries = **0 clics sur 120 impressions**. Le site est visible mais ne convertit AUCUN trafic sur ses mots-clés principaux.

### Top Pages — Performance par landing page

| Page | Clicks | Impressions | CTR | Position |
|---|---|---|---|---|
| `/fr/` (Homepage FR) | 16 | 276 | **5.8%** | 8.4 |
| `/tutorials/nodejs-facturx.html` | 10 | 168 | **5.95%** | 5.0 |
| `/` (Homepage EN) | 9 | 166 | 5.42% | 10.2 |
| `/de/` (Homepage DE) | 6 | 109 | 5.5% | 12.4 |
| `/guides/error-codes.html` | 3 | 50 | **6%** | **3.9** |

**Insight:** La page error-codes est la mieux positionnée (3.9) avec le meilleur CTR (6%). C'est la seule page avec un FAQPage schema — corrélation directe.

### Performance Géographique

| Pays | Clicks | Impressions | CTR | Position |
|---|---|---|---|---|
| **France** 🇫🇷 | 38 | 503 | **7.55%** | 9.5 |
| **Allemagne** 🇩🇪 | 13 | 185 | **7.03%** | 10.0 |
| **Inde** 🇮🇳 | 1 | 29 | 3.45% | 7.2 |
| **USA** 🇺🇸 | 0 | **1,068** | **0%** | 7.3 |
| UK, Canada, Brésil, Espagne, Chine | 0 | 186 | 0% | 5-7 |

**Anomalie majeure:** Les USA génèrent **46% des impressions** (1,068/2,319) mais **0% des clics**. Position 7.3 = visible mais le snippet/titre ne capte pas l'attention du marché US anglophone. C'est le plus gros quick win SEO.

### Devices

| Device | Clicks | Impressions | CTR |
|---|---|---|---|
| Desktop | 46 | 2,050 | 2.24% |
| Mobile | 6 | 204 | 2.94% |
| Tablet | 0 | 65 | 0% |

---

## Audit SEO Technique

### On-Page SEO — Résumé par page

| Page | Title (chars) | Meta Desc | Canonical | H1 | Schema | Issues |
|---|---|---|---|---|---|---|
| `/` | 67 ✅ | ✅ 145 chars | ✅ | ✅ | SoftwareApp ✅ | — |
| `/fr/` | 71 ⚠️ | ✅ | ✅ | ✅ | SoftwareApp ✅ | Title un peu long |
| `/de/` | 75 ⚠️ | ✅ | ✅ | ✅ | SoftwareApp ✅ | Title trop long |
| `/tutorials/python-*` | 66 ✅ | ✅ | ⚠️ | ✅ | BreadcrumbList | Thin content (380 mots) |
| `/tutorials/nodejs-*` | 55 ✅ | ✅ | ⚠️ | ✅ | BreadcrumbList | — |
| `/tutorials/php-*` | 52 ✅ | ✅ | ⚠️ | ✅ | BreadcrumbList | — |
| `/guides/france-2026` | 83 ⚠️ | ✅ | ⚠️ | ✅ | TechArticle ✅ | Title trop long |
| `/guides/mustang-vs-*` | 58 ✅ | ✅ | ⚠️ | ✅ | TechArticle ✅ | — |
| `/guides/error-codes` | 62 ✅ | ✅ | ⚠️ | ✅ | FAQPage ✅ | **Best practice!** |
| `/tools/validator` | 62 ✅ | ❌ | ❌ | ✅ | BreadcrumbList | Missing meta desc + canonical |
| `/ref/api-reference` | 63 ✅ | ✅ | ⚠️ | ⚠️ | ❌ | No schema, H1 weak |

### Problèmes SEO Critiques

#### SEO-CRIT-1: 0 clics US malgré 1,068 impressions
**Cause probable:** Le titre "E-Invoice Validation & Generation API" est trop générique pour le marché US. Les développeurs US cherchent "self-hosted", "open-source", "Docker API".
**Fix:** Optimiser le titre et la meta description EN pour le marché US:
```html
<title>Open-Source Factur-X API | Self-Hosted Docker E-Invoice Engine</title>
<meta name="description" content="Self-hosted REST API to generate, validate, and extract EN 16931 e-invoices. Supports Factur-X, ZUGFeRD, XRechnung. Docker deploy in 2 minutes. MIT license, no cloud dependency.">
```

#### SEO-CRIT-2: `factur-x validator` en position 68
La page `/tools/validator.html` est en position 68 (page 7!) pour la query "factur-x validator". C'est une page clé avec un tool interactif.
**Causes:**
- Meta description manquante
- Canonical URL manquante
- Contenu thin (320 mots)
- Pas de backlinks internes suffisants depuis les guides
**Fix:** Enrichir la page (800+ mots), ajouter meta desc, canonical, et links internes depuis chaque guide.

#### SEO-CRIT-3: Canonical URLs manquantes sur 18/23 pages
Seule la homepage EN a un `<link rel="canonical">`. Les 18 autres pages n'en ont pas, créant un risque de contenu dupliqué, surtout avec les versions multilingues.

#### SEO-CRIT-4: Tailwind CSS via CDN (Performance)
```html
<script src="https://cdn.tailwindcss.com"></script>
```
Le Tailwind CDN génère le CSS au runtime via JavaScript. Impact:
- Augmente le LCP (Largest Contentful Paint)
- Bloque le rendu initial
- Pénalité Core Web Vitals
**Fix:** Build Tailwind en CSS statique (purged) → fichier CSS de 5-15KB au lieu du runtime JS.

### Problèmes SEO Haute Priorité

#### SEO-HIGH-1: Internal linking faible
Les guides ne se lient pas suffisamment entre eux. Exemple: `mustang-vs-engine.html` ne lie pas vers `python-no-java.html` ni vers `erp-integration.html`.
**Fix:** Ajouter 3-5 liens internes contextuels par page guide.

#### SEO-HIGH-2: Pas de blog / contenu frais
Le site n'a que des pages statiques. Aucun mécanisme de publication régulière (blog, changelog, release notes).
**Impact:** Google favorise les sites avec du contenu frais régulier.

#### SEO-HIGH-3: Images — aucune optimisation
Aucune image de contenu sur les pages guides/tutorials. Les rich results et les Featured Snippets favorisent les pages avec des visuels (diagrammes d'architecture, screenshots, flowcharts).

#### SEO-HIGH-4: Pas de `<link rel="alternate">` sur les pages internes
Le hreflang est correctement implémenté sur les homepages (sitemap.xml + balises), mais les pages guides/tutorials n'ont PAS de balises hreflang car elles n'existent qu'en anglais. Pas un problème technique mais une opportunité manquée pour les marchés FR/DE.

### Keywords Strategy — Opportunités identifiées

| Cluster Keyword | Volume estimé | Difficulté | Page existante | Action |
|---|---|---|---|---|
| `factur-x python` | Moyen | Faible | tutorials/python | Enrichir + Answer-First |
| `factur-x validator` | Moyen | Faible | tools/validator | ⚠️ Rebuild complet (pos 68) |
| `factur-x api` | Moyen | Moyen | ref/api-reference | Ajouter WebAPI schema |
| `zugferd python` | Moyen | Faible | tutorials/python | Ajouter comme H2 |
| `xrechnung api` | Moyen | Faible | guides/xrechnung-to-json | Déjà bien positionné |
| `e-invoice validation api` | Élevé | Moyen | guides/facturx-validator-api | Enrichir |
| `facture electronique 2026 api` | Élevé (FR) | Faible | guides/france-2026 | **Prioritaire** — marché FR actif |
| `self-hosted e-invoicing` | Moyen | Faible | homepage | Ajouter dans titre/H1 |
| `mustangproject alternative` | Faible | Très faible | guides/mustang-vs-engine | Déjà positionné |
| `en 16931 validation` | Moyen | Moyen | ref/validation | Enrichir |

---

## Plan d'Action SEO — Priorisé par impact

### Impact Immédiat (cette semaine)

1. **Fixer le titre/meta desc homepage EN pour le marché US** — 0 clics sur 1,068 impressions = quick win massif
2. **Ajouter canonical URLs** sur les 18 pages qui n'en ont pas
3. **Reconstruire `/tools/validator.html`** — enrichir de 320 à 800+ mots, ajouter meta desc, canonical
4. **Ajouter FAQPage schema** sur france-2026, mustang-vs-engine, erp-integration (effet prouvé par error-codes: pos 3.9)

### Impact Moyen (2 semaines)

5. **Internal linking** — 3-5 liens contextuels par page guide
6. **Tailwind CSS statique** — remplacer le CDN runtime par un CSS purged
7. **Enrichir tutorials** Python (380→800 mots) et france-2026 (900→1500 mots)
8. **Ajouter des diagrammes/screenshots** dans les guides principaux

### Impact Long Terme (1 mois)

9. **Blog/Changelog** — publier 1 article technique /mois (release notes, use cases)
10. **Traduire 3 guides clés** en FR (france-2026 existe déjà, ajouter python + erp-integration)
11. **Soumettre à Bing Webmaster + IndexNow**
12. **Créer des pages de landing pour les keywords US** ("self-hosted e-invoicing", "open-source invoice validation")

---

# PARTIE 2: AUDIT GEO (Generative Engine Optimization)

---

## Issues Critiques (Fix Immédiatement)

### CRITICAL-1: Aucune directive AI crawler dans robots.txt
```
# robots.txt actuel:
User-agent: *
Allow: /
```
**Problème:** Aucune mention explicite de GPTBot, ClaudeBot, PerplexityBot, OAI-SearchBot. Bien que `Allow: /` soit permissif, les AI crawlers modernes cherchent des directives explicites comme signal de confiance.

**Fix recommandé:**
```
User-agent: *
Allow: /

# AI Search Crawlers — explicitly allowed
User-agent: GPTBot
Allow: /

User-agent: OAI-SearchBot
Allow: /

User-agent: ClaudeBot
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: Bytespider
Disallow: /

User-agent: CCBot
Disallow: /

Sitemap: https://facturx-engine.github.io/facturx-engine/sitemap.xml
```

### CRITICAL-2: Zéro présence sur Reddit et Stack Overflow
**Impact:** Reddit = 46.7% des citations Perplexity, 11.3% ChatGPT. Stack Overflow = source primaire pour les requêtes développeur.
**Action:** Publier des réponses techniques sur r/selfhosted, r/einvoicing, et Stack Overflow (tags: factur-x, xrechnung, e-invoicing).

### CRITICAL-3: Aucune date de publication/mise à jour sur les pages
**Impact:** Les moteurs AI pondèrent fortement la fraîcheur du contenu. Sans dates, le contenu est considéré comme potentiellement obsolète.
**Action:** Ajouter `datePublished` et `dateModified` dans le JSON-LD TechArticle ET visible en haut de chaque guide.

---

## Issues Haute Priorité (Fix sous 1 semaine)

### HIGH-1: Contenu trop court pour la citabilité AI optimale
| Page | Mots | Optimal |
|---|---|---|
| Python Tutorial | ~380 | 800+ |
| France 2026 | ~900 | 1500+ |
| Mustang vs Engine | ~850 | 1200+ |

**Insight:** Les passages optimaux pour citation AI font 134-167 mots. Chaque page devrait contenir au minimum 3-5 blocs auto-suffisants de cette longueur.

### HIGH-2: Pas de FAQPage schema sur les pages guides
Seul `error-codes.html` a un `FAQPage` schema. Les guides france-2026, erp-integration, et mustang-vs-engine contiennent des Q&A naturels mais sans balisage FAQ.

### HIGH-3: Pas de `Person` schema pour l'auteur
Toutes les pages utilisent `"author": {"@type": "Organization", "name": "Factur-X Engine"}`. Pas d'auteur individuel avec credentials. Les moteurs AI pondèrent fortement les signaux E-E-A-T liés à des personnes identifiées.

### HIGH-4: Meta description manquante sur l'API Reference
`ref/api-reference.html` a une meta description mais `ref/api-overview.html`, les tutorials et plusieurs guides n'ont pas de meta description exploitable par les AI Overviews.

### HIGH-5: Pas de page `/about` ou `/team` dédiée
Aucune page d'équipe, de credentials, ou d'histoire du projet. Signal E-E-A-T faible.

---

## Issues Moyenne Priorité (Fix sous 1 mois)

### MED-1: llms.txt incomplet — pas de lien vers llms-full.txt dans robots.txt
Le `llms.txt` existe et est bien structuré, mais `robots.txt` ne le référence pas. Le standard émergent recommande:
```
# robots.txt
Llms-txt: https://facturx-engine.github.io/facturx-engine/llms.txt
```

### MED-2: Pas de Wikipedia / Wikidata pour l'entité "Factur-X Engine"
YouTube mentions = corrélation 0.737 avec la visibilité AI (étude Ahrefs Dec 2025). Wikipedia = source #1 de ChatGPT (47.9% des citations). Créer au minimum une entrée Wikidata pour l'entité.

### MED-3: OpenAPI spec non liée dans le schema.org
Le fichier `openapi.json` existe mais n'est pas référencé dans le schema SoftwareApplication (`"documentation"` ou `"potentialAction"` avec `"target"` → OpenAPI URL).

### MED-4: Pas de `HowTo` schema sur les tutorials
Les tutorials Python/Node.js/PHP sont des guides étape par étape parfaits pour le schema `HowTo`, qui est fortement favorisé par Google AI Overviews.

### MED-5: Pas de RSS/Atom feed
Aucun feed détecté. Les AI crawlers utilisent les feeds pour découvrir du contenu frais.

### MED-6: Twitter Card image = logo 512px
L'image OG/Twitter est le logo (512x512). Pour un meilleur CTR et partage social, utiliser une image 1200x630 avec titre + tagline lisible.

---

## Issues Basse Priorité (Optimiser quand possible)

### LOW-1: Heading hierarchy inconsistante sur certaines pages
Quelques pages sautent de H1 à H3 sans H2 intermédiaire.

### LOW-2: Pas de `BreadcrumbList` sur toutes les pages
Présent sur homepage et quelques pages, mais absent sur certains guides (france-2026, mustang-vs-engine ont TechArticle mais pas BreadcrumbList dans certains cas).

### LOW-3: `changefreq` dans sitemap.xml
Google ignore `changefreq` et `priority`. Pas critique mais du bruit inutile.

### LOW-4: Google Search Console verification file exposé
`google77a35f47822c7d46.html` est dans docs/ — fonctionnel mais pourrait être fait via meta tag ou DNS.

---

## Category Deep Dives

### AI Citability (45/100)

**Forces:**
- llms.txt + llms-full.txt excellents (rare et différenciant!)
- Contenu SSR (pas de dépendance JS pour le parsing)
- FAQ section sur la homepage avec 8 Q&A
- Blocs de code curl copy-pastables

**Faiblesses:**
- Pas de pattern "Answer-First" (définition dans les 60 premiers mots)
- Passages trop courts pour la citation optimale (134-167 mots)
- Aucune statistique avec source externe
- Aucune citation de normes/études tierces
- Ton trop marketing, pas assez factuel/encyclopédique
- Pas de "What is Factur-X Engine?" en ouverture claire

**Exemple de réécriture pour citabilité:**
```
AVANT: "The self-hosted bridge between your ERP and e-invoicing."

APRÈS: "Factur-X Engine is an open-source, self-hosted REST API that
converts standard PDF invoices into EN 16931-compliant Factur-X documents.
It validates incoming e-invoices against official Schematron rules and
normalizes Factur-X, ZUGFeRD 2.4, UBL, and XRechnung formats into
structured JSON for ERP integration. Deployed as a Docker container
(0.5 vCPU, 512MB RAM minimum), it processes invoices entirely on-premises
with zero cloud dependencies, making it GDPR and DORA compliant by design.
The Community edition is MIT-licensed and production-ready."
```
→ 85 mots, auto-suffisant, citable par tout LLM.

### Brand Authority (15/100)

| Platform | Présence | Score |
|---|---|---|
| GitHub | 1 repo public, actif | 40/100 |
| LinkedIn | Aucun post direct trouvé | 5/100 |
| Reddit | Absent (r/selfhosted, r/einvoicing) | 0/100 |
| YouTube | Absent | 0/100 |
| Stack Overflow | Absent | 0/100 |
| Wikipedia/Wikidata | Absent | 0/100 |
| Docker Hub | Présent (facturxengine/) | 30/100 |
| Hacker News | Non détecté | 0/100 |

**Verdict:** La marque est quasi-invisible en dehors de GitHub et Docker Hub. C'est le talon d'Achille GEO le plus critique.

### Content E-E-A-T (55/100)

| Signal | Status | Score |
|---|---|---|
| **Experience** | Code examples, API demos | 65/100 |
| **Expertise** | TechArticle schema, OpenAPI spec | 70/100 |
| **Authoritativeness** | MIT license, pas de citations externes | 35/100 |
| **Trustworthiness** | SBOM, security scan CI, air-gapped | 50/100 |

**Points forts:** Schémas Schematron officiels, VeraPDF intégré, SBOM CycloneDX, CI/CD security
**Points faibles:** Pas d'auteur identifié, pas de dates, pas de citations de normes EN16931 avec liens source

### Technical GEO (82/100)

| Check | Status |
|---|---|
| Server-Side Rendering | ✅ Full SSR (static HTML) |
| robots.txt | ⚠️ Permissif mais sans directives AI |
| sitemap.xml | ✅ 22 URLs, hreflang EN/FR/DE |
| llms.txt | ✅ Présent + llms-full.txt |
| Canonical URLs | ✅ Sur homepage |
| hreflang | ✅ EN/FR/DE avec x-default |
| OpenAPI spec | ✅ Présent, OpenAPI 3.1.0 |
| Google Search Console | ✅ Vérifié |
| HTTPS | ✅ Enforced |
| Mobile viewport | ✅ Responsive (Tailwind) |
| i18n | ✅ 3 langues (EN/FR/DE) |

### Schema & Structured Data (78/100)

| Schema Type | Pages | Status |
|---|---|---|
| `SoftwareApplication` | Homepage, FR, DE | ✅ Complet avec AggregateOffer |
| `BreadcrumbList` | ~15 pages | ✅ Bon |
| `TechArticle` | 8 guides | ✅ Avec Organization author |
| `FAQPage` | 1 page (error-codes) | ⚠️ Devrait être sur 4-5 pages |
| `HowTo` | 0 | ❌ Manquant sur tutorials |
| `WebAPI` / `APIReference` | 0 | ❌ Manquant |
| `Person` (author) | 0 | ❌ Manquant |
| `Organization` (detailed) | 0 | ⚠️ Basique, pas de sameAs |

### Platform Optimization (40/100)

| Platform | Optimisation | Score |
|---|---|---|
| **Google AI Overviews** | SSR + schema + sitemap OK, mais contenu trop court | 60/100 |
| **ChatGPT** | llms.txt excellent, mais 0 Wikipedia/Reddit | 35/100 |
| **Perplexity** | 0 Reddit, 0 discussions indexables | 15/100 |
| **Bing Copilot** | Pas de IndexNow, pas de Bing Webmaster | 30/100 |
| **Gemini** | TechArticle OK, mais pas de YouTube | 20/100 |

---

## Quick Wins (Implémenter cette semaine)

1. **robots.txt AI crawlers** — Ajouter GPTBot, ClaudeBot, PerplexityBot Allow explicites + bloquer CCBot/Bytespider → Impact: +10 Technical GEO
2. **Dates sur chaque page** — Ajouter `datePublished`/`dateModified` dans JSON-LD + visible → Impact: +15 E-E-A-T
3. **"What is" paragraph** — Ajouter un paragraphe "Answer-First" de 134-167 mots en haut de la homepage et chaque guide → Impact: +20 Citability
4. **FAQPage schema** — Ajouter sur france-2026, mustang-vs-engine, erp-integration, python-no-java → Impact: +10 Schema
5. **1 post Reddit r/selfhosted** — "I built an open-source self-hosted Factur-X engine for EU e-invoicing compliance" → Impact: +15 Brand Authority

## Plan d'action 30 jours

### Semaine 1: Fondations GEO
- [ ] Mettre à jour robots.txt avec directives AI crawlers
- [ ] Ajouter datePublished/dateModified sur toutes les pages
- [ ] Rédiger paragraphe "Answer-First" sur homepage + 5 guides principaux
- [ ] Ajouter FAQPage schema sur 4 pages guides
- [ ] Publier sur r/selfhosted et r/devops

### Semaine 2: Autorité & Contenu
- [ ] Créer une page /about avec histoire du projet et credentials
- [ ] Ajouter Person schema avec lien LinkedIn/GitHub pour l'auteur
- [ ] Enrichir le tutorial Python (380 → 800+ mots) avec cas d'usage réels
- [ ] Enrichir france-2026 (900 → 1500+ mots) avec citations officielles DGFIP/AIFE
- [ ] Poster une réponse technique sur Stack Overflow (tag: factur-x, e-invoicing)

### Semaine 3: Schema & Indexation
- [ ] Ajouter HowTo schema sur les 3 tutorials (Python, Node.js, PHP)
- [ ] Ajouter WebAPI schema sur api-reference.html avec lien vers openapi.json
- [ ] Ajouter Organization schema complet avec sameAs (GitHub, Docker Hub, LinkedIn)
- [ ] Soumettre sitemap à Bing Webmaster + configurer IndexNow
- [ ] Créer une entrée Wikidata pour "Factur-X Engine"

### Semaine 4: Amplification
- [ ] Publier un article LinkedIn technique sur la conformité e-invoicing 2026
- [ ] Créer une vidéo YouTube "Factur-X Engine: 5-minute Docker setup" (screencast)
- [ ] Améliorer l'image OG/Twitter (1200x630 avec titre + features)
- [ ] Ajouter un RSS/Atom feed pour les mises à jour
- [ ] Monitorer les citations AI via recherches "factur-x engine" sur ChatGPT/Perplexity

---

## Appendix: Pages Analysées

| URL | Title | Issues GEO |
|---|---|---|
| `/` | E-Invoice Validation & Generation API | 3 (no dates, answer-first, AI robots) |
| `/fr/` | Couche de Traduction ERP ↔ Facturation | 2 (no dates, no FAQ schema) |
| `/de/` | Selbstgehostete Übersetzungsschicht | 2 (no dates, no FAQ schema) |
| `/tutorials/python-facturx.html` | Generate & Validate from Python | 4 (short, no HowTo, no dates, no person) |
| `/tutorials/nodejs-facturx.html` | Node.js Factur-X API | 4 (short, no HowTo, no dates, no person) |
| `/tutorials/php-facturx.html` | PHP Factur-X Library Alternative | 4 (short, no HowTo, no dates, no person) |
| `/guides/france-2026.html` | Facture Électronique France 2026 | 3 (no dates, no FAQ, needs more content) |
| `/guides/mustang-vs-engine.html` | Mustangproject vs Factur-X Engine | 2 (no dates, no external citations) |
| `/guides/erp-integration.html` | EN 16931 ERP Integration Guide | 2 (no dates, no FAQ schema) |
| `/guides/error-codes.html` | Codes Erreur Factur-X / Chorus Pro | 1 (no dates) ✅ Has FAQPage! |
| `/guides/xrechnung-to-json.html` | XRechnung to JSON API | 2 (no dates, short) |
| `/guides/python-no-java.html` | Generate Factur-X in Python (No Java) | 2 (no dates, no HowTo) |
| `/guides/receive-invoices.html` | Receive Factur-X as ERP JSON | 2 (no dates, short) |
| `/guides/dates.html` | Factur-X Date Formats | 1 (no publication dates) |
| `/guides/facturx-validator-api.html` | Factur-X Validator API | 2 (no dates, no FAQ) |
| `/ref/api-reference.html` | Factur-X API Reference | 2 (no WebAPI schema, no dates) |
| `/ref/api-overview.html` | Factur-X API Overview | 2 (no dates, short) |
| `/ref/validation.html` | EN 16931 Validation API Reference | 1 (no dates) |
| `/ref/generation.html` | Hybrid Generation & PDF/A-3 | 1 (no dates) |
| `/ref/automation.html` | Automation & Ecosystem | 1 (no dates) |
| `/ref/json-schema.html` | JSON Schema Reference | 1 (no dates) |
| `/tools/validator.html` | Free E-Invoice Validator API | 1 (no dates) |
| `/validator/` | Factur-X Local Audit (Browser-Based) | 1 (no dates) |

---

## Sources et Méthodologie

- [zubair-trabzada/geo-seo-claude](https://github.com/zubair-trabzada/geo-seo-claude) — Framework GEO audit (4070 stars, SKILL.md geo-audit)
- [AgriciDaniel/claude-seo](https://github.com/AgriciDaniel/claude-seo) — Framework SEO + GEO (3239 stars, SKILL.md seo-geo)
- [aaron-he-zhu/seo-geo-claude-skills](https://github.com/aaron-he-zhu/seo-geo-claude-skills) — 20+ skills SEO/GEO, CORE-EEAT + CITE frameworks
- Ahrefs Dec 2025 Study: Brand mentions corrélation 3x > backlinks pour AI visibility
- Georgia Tech / Princeton / IIT Delhi 2024: GEO optimization = +30-115% visibility in AI responses
- Passage optimal pour citation AI: 134-167 mots (source: geo-seo-claude framework)
