
from pathlib import Path

import pytest

from app.services.hybrid_validation_service import HybridValidationService

# Path to corpus
CORPUS_DIR = Path(__file__).parent / "corpus"

# Files to skip (not Factur-X/CII invoices)
SKIP_FILES = {
    "bare_invoice.pdf",  # Plain PDF without embedded XML
}

# Directories containing macOS resource forks (not real files)
EXCLUDE_DIRS = {"__MACOSX"}


def get_corpus_files(subdir):
    """Recursively yield all PDF and XML files in a subdirectory."""
    target_dir = CORPUS_DIR / subdir
    if not target_dir.exists():
        return []
    return [
        f for f in target_dir.rglob("*")
        if f.is_file()
        and f.suffix.lower() in ('.pdf', '.xml')
        and not any(excl in f.parts for excl in EXCLUDE_DIRS)
    ]


# --- Core corpus: hand-curated valid/invalid files ---

@pytest.mark.parametrize("file_path", get_corpus_files("valid"))
def test_valid_corpus_files(file_path):
    """Ensure all files in tests/corpus/valid/ are considered valid."""
    if file_path.name in SKIP_FILES:
        pytest.skip(f"{file_path.name} is not a Factur-X file")

    content = file_path.read_bytes()
    # Use HybridValidationService (Production Engine)
    result = HybridValidationService.validate(content, file_path.name)
    
    is_valid = result["is_valid"]
    errors = result.get("errors", [])

    assert is_valid is True, f"Expected {file_path.name} to be VALID but got errors: {errors}"



# --- Extended corpus: ZUGFeRD 2.4 official examples ---

ZUGFERD_DIR = CORPUS_DIR / "ZUGFeRD-2.4-examples"

def get_zugferd_pdf_files():
    """Get all PDF files from ZUGFeRD 2.4 examples."""
    if not ZUGFERD_DIR.exists():
        return []
    return [
        f for f in ZUGFERD_DIR.rglob("*.pdf")
        if f.is_file()
        and not any(excl in f.parts for excl in EXCLUDE_DIRS)
    ]

@pytest.mark.parametrize("file_path", get_zugferd_pdf_files())
def test_zugferd_24_pdf_corpus(file_path):
    """Validate all ZUGFeRD 2.4 official example PDFs are parseable."""
    content = file_path.read_bytes()
    # Use HybridValidationService (Production Engine)
    result = HybridValidationService.validate(content, file_path.name)
    
    is_valid = result["is_valid"]
    errors = result.get("errors", [])

    # Strict check: Official examples SHOULD be valid
    # Invalid files have been deleted from the corpus
    assert is_valid is True, f"ZUGFeRD 2.4 example {file_path.name} failed validation: {errors}"


# --- Extended corpus: XRechnung 3.0.2 test suite ---

XRECHNUNG_DIR = CORPUS_DIR / "xrechnung-3.0.2-testsuite-2025-07-10" / "instances"

def get_xrechnung_cii_files():
    """Get CII (CrossIndustryInvoice) XML files from XRechnung 3.0.2 test instances."""
    if not XRECHNUNG_DIR.exists():
        return []
    files = []
    for f in XRECHNUNG_DIR.rglob("*.xml"):
        if not f.is_file():
            continue
        try:
            head = f.read_bytes()[:500]
            if b"CrossIndustryInvoice" in head:
                files.append(f)
        except Exception:
            pass
    return files


def get_xrechnung_ubl_files():
    """Get UBL XML files from XRechnung 3.0.2 test instances."""
    if not XRECHNUNG_DIR.exists():
        return []
    files = []
    for f in XRECHNUNG_DIR.rglob("*.xml"):
        if not f.is_file():
            continue
        try:
            head = f.read_bytes()[:500]
            if b"CrossIndustryInvoice" not in head and (b"Invoice" in head or b"CreditNote" in head):
                files.append(f)
        except Exception:
            pass
    return files


@pytest.mark.parametrize("file_path", get_xrechnung_cii_files())
def test_xrechnung_302_cii_corpus(file_path):
    """Validate CII-format XRechnung 3.0.2 test instances."""
    content = file_path.read_bytes()
    # Use HybridValidationService (Production Engine)
    result = HybridValidationService.validate(content, file_path.name)
    
    is_valid = result["is_valid"]
    errors = result.get("errors", [])

    # XRechnung files SHOULD be valid
    assert is_valid is True, f"XRechnung CII file {file_path.name} failed: {errors}"


@pytest.mark.parametrize("file_path", get_xrechnung_ubl_files())
def test_xrechnung_302_ubl_corpus(file_path):
    """Validate UBL-format XRechnung 3.0.2 test instances with EN16931 Schematron."""
    content = file_path.read_bytes()
    result = HybridValidationService.validate(content, file_path.name)

    is_valid = result["is_valid"]
    errors = result.get("errors", [])
    assert is_valid is True, f"XRechnung UBL file {file_path.name} failed: {errors}"


# --- Corpus Master: ZUGFeRD v2 (Structured Valid/Invalid) ---

CORPUS_MASTER_DIR = CORPUS_DIR / "corpus-master" / "ZUGFeRDv2"

def get_master_correct_files():
    """Get files from corpus-master/ZUGFeRDv2/correct (Must be Valid)."""
    if not CORPUS_MASTER_DIR.exists():
        return []
    return [
        f for f in (CORPUS_MASTER_DIR / "correct").rglob("*")
        if f.is_file() and f.suffix.lower() in ('.pdf', '.xml')
    ]

def get_master_fail_files():
    """Get files from corpus-master/ZUGFeRDv2/fail (Must be Invalid)."""
    if not CORPUS_MASTER_DIR.exists():
        return []
    return [
        f for f in (CORPUS_MASTER_DIR / "fail").rglob("*")
        if f.is_file() and f.suffix.lower() in ('.pdf', '.xml')
    ]

@pytest.mark.parametrize("file_path", get_master_correct_files())
def test_master_zugferd_v2_correct(file_path):
    """Verify files in 'correct' folder are Valid."""
    content = file_path.read_bytes()
    result = HybridValidationService.validate(content, file_path.name)
    
    # We deleted all known invalid files from this folder.
    # So EVERYTHING left should be valid.
    assert result["is_valid"] is True, f"Expected {file_path.name} to be VALID but failed: {result.get('errors')}"



if __name__ == "__main__":
    # Allow running directly to see what files are picked up
    print(f"Scanning {CORPUS_DIR}...")
    valid_files = get_corpus_files("valid")
    invalid_files = get_corpus_files("invalid")
    zugferd_pdfs = get_zugferd_pdf_files()
    xrechnung_cii = get_xrechnung_cii_files()
    xrechnung_ubl = get_xrechnung_ubl_files()
    print(f"Found {len(valid_files)} valid test files.")
    print(f"Found {len(invalid_files)} invalid test files.")
    print(f"Found {len(zugferd_pdfs)} ZUGFeRD 2.4 PDFs.")
    print(f"Found {len(xrechnung_cii)} XRechnung 3.0.2 CII XMLs.")
    print(f"Found {len(xrechnung_ubl)} XRechnung 3.0.2 UBL XMLs.")
