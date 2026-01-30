import pytest
import os
from pathlib import Path
from app.services.validator import ValidationService

# Path to corpus
CORPUS_DIR = Path(__file__).parent / "corpus"

def get_corpus_files(subdir):
    """Recursively yield all PDF and XML files in a subdirectory."""
    target_dir = CORPUS_DIR / subdir
    if not target_dir.exists():
        return []
    return [
        f for f in target_dir.rglob("*") 
        if f.is_file() and f.suffix.lower() in ('.pdf', '.xml')
    ]

@pytest.mark.parametrize("file_path", get_corpus_files("valid"))
def test_valid_corpus_files(file_path):
    """Ensure all files in tests/corpus/valid/ are considered valid."""
    if file_path.name == "bare_invoice.pdf":
        pytest.skip("bare_invoice.pdf is a plain PDF, not a Factur-X file")

    print(f"Testing valid file: {file_path.name}")
    content = file_path.read_bytes()
    is_valid, fmt, flavor, errors = ValidationService.validate_file(content, file_path.name)
    
    assert is_valid is True, f"Expected {file_path.name} to be VALID but got errors: {errors}"
    assert fmt is not None

@pytest.mark.parametrize("file_path", get_corpus_files("invalid"))
def test_invalid_corpus_files(file_path):
    """Ensure all files in tests/corpus/invalid/ are considered invalid."""
    print(f"Testing invalid file: {file_path.name}")
    content = file_path.read_bytes()
    is_valid, fmt, flavor, errors = ValidationService.validate_file(content, file_path.name)
    
    assert is_valid is False, f"Expected {file_path.name} to be INVALID but it passed."

if __name__ == "__main__":
    # Allow running directly to see what files are picked up
    print(f"Scanning {CORPUS_DIR}...")
    valid_files = get_corpus_files("valid")
    invalid_files = get_corpus_files("invalid")
    print(f"Found {len(valid_files)} valid test files.")
    print(f"Found {len(invalid_files)} invalid test files.")
