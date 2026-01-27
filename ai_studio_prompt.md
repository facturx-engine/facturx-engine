**Role:** Expert Web Designer & SEO Specialist.

**Task:** Create a responsive, single-file HTML landing page for a backend software product called "Factur-X Engine".

**Product Context:**
"Factur-X Engine" is a high-performance, stateless Docker container used by developers, banks, and enterprises. It allows generating and validating electronic invoices (Factur-X, ZUGFeRD, XRechnung) locally, without internet access (Air-gapped).

**Technical Requirements:**

1. **Single File Architecture**: The output must be a single `index.html` file.
2. **Stack**: Use **Tailwind CSS** (via CDN script) for styling. No external CSS files or build steps.
3. **Performance**: Ensure the layout is lightweight and loads instantly.

**SEO & Content Requirements (Crucial):**

1. **Meta Data**: Include optimized Title, Description, and Keywords targeting: "Factur-X", "ZUGFeRD 2.4", "XRechnung 3.0", "Python PDF/A-3", "Docker Invoice API".
2. **Structured Data**: Embed **JSON-LD** schema for `SoftwareApplication`, including `operatingSystem="Docker"` and `applicationCategory="BusinessApplication"`.
3. **Copywriting**:
    - **Headline**: Something powerful about "Standard Compliance" and "Performance".
    - **Key Selling Points**:
        - **Air-Gapped / Security**: No data leaves the server.
        - **Zero Dependencies**: Pure Python, no Java/JVM, no Ghostscript.
        - **Native Compliance**: Built-in logical validation (Schematron) for EN 16931.
    - **Call to Actions**: Links to `/docs` (API Docs), `/health` (System Status), and GitHub.

**Design Guidelines:**

- ❌ **NO DIRECTIVES**: I am specifically **NOT** giving you color codes, layout instructions, or style preferences (e.g. no "make it blue", no "make it dark").
- ✅ **GOAL**: Produce a **visually stunning, "State of the Art" UI**. It should feel incredibly premium, trustworthy, and modern (think top-tier DevTools or Infrastructure SaaS).
- **Animations**: Feel free to use CSS animations or Tailwind utilities to make it feel "alive" and polished.

**Output:**
Return the complete, ready-to-use `index.html` code.
