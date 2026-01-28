"""
License verification for Factur-X Engine Pro.

Simple Ed25519 signature verification without Cython complexity.
The real protection is in the value of the service, not code obfuscation.
"""
import os
import logging
import json
import base64
import time
import hashlib
import threading
from datetime import datetime
import nacl.signing
import nacl.encoding
import nacl.exceptions

logger = logging.getLogger(__name__)

from app.constants import LICENSE_SALT

# Public Key for license verification (XOR obfuscated)
_XOR_SEED = hashlib.sha256(LICENSE_SALT).digest()
_OBFUSCATED_KEY_HEX = "7fd1630e5f5a90228cfd243234ec497c1e174dca9aacb5d5f596666197b54985"


def _deobfuscate_key() -> str:
    """Runtime de-obfuscation of public key."""
    obf_bytes = bytes.fromhex(_OBFUSCATED_KEY_HEX)
    real_bytes = bytes([a ^ b for a, b in zip(obf_bytes, _XOR_SEED)])
    return real_bytes.hex()


# Cache with TTL
_license_cache = {"valid": None, "expires": 0, "key_hash": None}
_cache_lock = threading.Lock()


def _verify_license_crypto(license_key_b64: str) -> bool:
    """Verify Ed25519 signed license payload."""
    try:
        verify_key_hex = _deobfuscate_key()
        verify_key = nacl.signing.VerifyKey(verify_key_hex, encoder=nacl.encoding.HexEncoder)
        
        try:
            signed_data = base64.b64decode(license_key_b64, validate=True)
        except Exception:
            logger.error("License Key is not valid Base64.")
            return False

        payload_bytes = verify_key.verify(signed_data)
        payload = json.loads(payload_bytes.decode('utf-8'))
        
        # Validate required fields
        required_fields = ["sub", "exp", "tier"]
        if not all(field in payload for field in required_fields):
            logger.error(f"License payload missing fields: {[f for f in required_fields if f not in payload]}")
            return False
            
        # Check expiry
        expiry_str = payload.get("exp")
        try:
            expiry_date = datetime.strptime(expiry_str, "%Y-%m-%d")
            if datetime.now() > expiry_date:
                logger.warning(f"License expired on {expiry_str}. Pro features disabled.")
                return False
        except ValueError:
            logger.error("Invalid date format in license.")
            return False
            
        logger.info(f"License verified: {payload.get('sub')} [{payload.get('tier')}] valid until {expiry_str}")
        return True

    except nacl.exceptions.BadSignatureError:
        logger.error("License signature verification FAILED.")
        return False
    except Exception as e:
        logger.error(f"License check error: {e}")
        return False


def is_licensed() -> bool:
    """
    Check if a valid Pro license is present.
    Thread-safe with caching for performance.
    """
    now = time.time()
    license_key_b64 = os.getenv("LICENSE_KEY", "").strip()
    key_hash = hashlib.sha256(license_key_b64.encode()).hexdigest()
    
    # Fast path: check cache
    with _cache_lock:
        if (_license_cache["expires"] > now and 
            _license_cache["key_hash"] == key_hash):
            return _license_cache["valid"]
    
    # No license key = Community mode
    if not license_key_b64:
        logger.info("No LICENSE_KEY found. Running in Community mode.")
        with _cache_lock:
            _license_cache["valid"] = False
            _license_cache["expires"] = now + 300  # Cache for 5 min
            _license_cache["key_hash"] = key_hash
        return False

    # Verify license (slow path)
    is_valid = _verify_license_crypto(license_key_b64)

    # Update cache
    with _cache_lock:
        _license_cache["valid"] = is_valid
        _license_cache["expires"] = now + 60  # Cache for 1 min
        _license_cache["key_hash"] = key_hash
    
    return is_valid
