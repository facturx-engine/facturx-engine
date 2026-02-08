"""
Trial Service for Factur-X Engine.
Enables Pro features for a whitelist of standard reference/demo files.
"""
import hashlib
from typing import Set

# MD5 Hashes of standard reference files (from tests/corpus/valid/)
# These files unlock Pro features (Smart Diagnostics & Full JSON Serialization) 
# even without a license key.
DEMO_WHITELIST: Set[str] = {
    "a0db0603cea39130ce4fd5ad56c2f5a1",  # Facture_FR_MINIMUM.pdf
    "ede0959005841756ec3bd4555f19fc3b",  # Facture_FR_BASICWL.pdf
    "cf38dd97d02a73b8a671271cebf48301",  # ZUGFeRD_2.4_EN16931.pdf
    "e2ab861ee350ca3f6cc1c517e6dfe4fc",  # ZUGFeRD_2.4_MINIMUM.pdf
}

def is_trial_file(file_content: bytes) -> bool:
    """Check if the provided file content matches a whitelisted demo file."""
    if not file_content:
        return False
    
    file_hash = hashlib.md5(file_content).hexdigest()
    return file_hash in DEMO_WHITELIST

def get_trial_file_info(file_content: bytes) -> dict:
    """Return info about why this file is allowed (for UI/API notices)."""
    if is_trial_file(file_content):
        return {
            "is_trial": True,
            "message": "Trial Mode: This reference file has unlocked Pro features for demonstration."
        }
    return {"is_trial": False}
