# 🧪 Pyodide Feasibility Study: "Zero-Upload Validator"

**Goal:** A "Zero-Upload" Validator & Demo tool running in the browser.
**Strategy Invariant:** The POC must demonstrate power ("Wow Effect") without replacing the Pro Engine.

- **Validation:** Free & Unlimited (Trust Builder).
- **Extraction:** Preview Only (JSON visible, Single File). No Batch/API.
- **Conversion:** Demo Only (Watermarked "NON VALABLE", degraded data).

**Tech Stack:** Pyodide (Python in WASM), standard HTML/JS.

## 1. Dependency Analysis (The Critical Path)

Our engine relies on C-Extension libraries. These must be pre-compiled for WASM by the Pyodide team or built manually.

| Dependency | Purpose | Pyodide Status | Risk |
| :--- | :--- | :--- | :--- |
| **`lxml`** | XML Parsing & XSD Validation | ✅ Supported (Official) | Low |
| **`factur-x`** | PDF/A-3 Extraction | ⚠️ Pure Python? | Low (Check deps) |
| **`pypdf`** | PDF Manipulation | ✅ Pure Python | Low |
| **`reportlab`** | PDF Generation | ✅ Supported (Official) | Low |
| **`xmlschema`** | XSD Validation | ✅ Pure Python | Low |
| **`requests`** | Networking | ❌ Not supported (Use `pyodide.http`) | Medium (We need to mock it or avoid it) |

> **Critical Check:** Does `factur-x` library import anything that requires sockets or threading? (Validation should be mostly CPU bound).

## 2. The Prototype Plan

### Step A: The "Hello World"

Create a simple `index.html` that:

1. Loads Pyodide CDN.
2. `micropip.install("lxml")`.
3. Parses a dummy XML string.

### Step B: The "Factur-X" Load

1. Upload our proprietary code (or a subset of it) to the virtual filesystem?
   - *Better:* Just install the open source `factur-x` lib from PyPI.
2. Run the `factur-x` extraction logic on a buffer.

### Step C: The Validator UI

1. File Input (Drag & Drop PDF).
2. Convert JS File/Blob -> Python Bytes.
3. Run Validation.
4. Display Result (JSON) in HTML.

### Step D: The "Factur-X" Generator (Demo Mode)

1. **Pivot**: Switched from `factur-x` library (which failed with filesystem errors) to **pure `pypdf`**.
2. **Compliance**: Achieved 100% PDF/A-3 and Factur-X compliance by manually injecting:
    - XMP Metadata (Factur-X Extension Schema v1.0).
    - OutputIntent (sRGB ICC profile).
    - Associated Files (AF) relationship.
3. **Sabotage**: XML data is hardcoded with "DEMO" values to prevent production use.

## 3. Roadblocks & Mitigation

- **Load Time:** Pyodide is heavy (~10MB+).
  - *Mitigation:* Use specialized CDN, cache heavily. It's a "Tool" page, users expect a loading spinner.
- **XSD Files:** The validator needs access to `.xsd` files.
  - *Mitigation:* We need to package these XSDs into a `.whl` or download them into the virtual FS at startup.
- **Generation FileSystem Errors:** `[Errno 44] No such file or directory` with standard lib.
  - *Solution:* Bypass FS entirely using in-memory `pypdf` generation.
- **XMP Validation Strictness:** Validators failing on namespace/schema definitions.
  - *Solution:* Manually injected exact 100-line XML template matching strict ISO specs.

## 4. Final Outcome (2026-01-20)

✅ **PROJECT COMPLETE.**
The POC successfully validates, extracts, and generates compliant Factur-X files entirely in the browser.
Status: **Platinum** (Passes FNFE/veraPDF validation).
