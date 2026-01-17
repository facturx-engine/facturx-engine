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
# HARDCODED PUBLIC KEY (Obfuscated XOR)
# Real Key: 5e78a793037512905464c0d3d6fd5aa43709aba0c9e8e4c6fb09210c69f3045b
# We store it obfuscated to prevent simple 'strings' command extraction
# XOR Key: LICENSE_SALT
_XOR_SEED = hashlib.sha256(LICENSE_SALT).digest()
_OBFUSCATED_KEY_HEX = "b745c7f0cf74d797afa510dc25622f5ea6f5ec8a77f2d81a0f522325b04466c5"

BUILD_DATE = "BUILD_DATE_PLACEHOLDER"

# Runtime De-obfuscation (Simple XOR)
def _deobfuscate_key() -> str:
    obf_bytes = bytes.fromhex(_OBFUSCATED_KEY_HEX)
    real_bytes = bytes([a ^ b for a, b in zip(obf_bytes, _XOR_SEED)])
    return real_bytes.hex()

# Manual cache with TTL and Thread Lock
_license_cache = {"valid": None, "expires": 0, "key_hash": None}
_cache_lock = threading.Lock()

def _verify_license_crypto(license_key_b64: str, build_date: str) -> bool:
    """Helper to perform the heavy lifting of crypto verification."""
    try:
        # Use De-obfuscated key
        verify_key_hex = _deobfuscate_key()
        verify_key = nacl.signing.VerifyKey(verify_key_hex, encoder=nacl.encoding.HexEncoder)
        
        # Decode Base64 STRICTLY
        try:
            signed_data = base64.b64decode(license_key_b64, validate=True)
        except Exception:
            logger.error("License Key is not valid Base64 (Corruption detected).")
            return False

        # Verify Signature
        payload_bytes = verify_key.verify(signed_data)
        
        # Parse JSON
        payload = json.loads(payload_bytes.decode('utf-8'))
        
        # STRICT Payload Validation
        required_fields = ["sub", "exp", "tier"]
        if not all(field in payload for field in required_fields):
            logger.error(f"License payload malformed. Missing fields: {[f for f in required_fields if f not in payload]}")
            return False
            
        # Check Expiry (Perpetual Fallback Logic)
        expiry_str = payload.get("exp")
        try:
            expiry_date = datetime.strptime(expiry_str, "%Y-%m-%d")
            # BUILD_DATE is injected at compile time via sed
            if build_date != "BUILD_DATE_PLACEHOLDER":
                build_date_obj = datetime.strptime(build_date, "%Y-%m-%d")
                
                if build_date_obj > expiry_date:
                    logger.error(f"Maintenance expired on {expiry_str}. This version built on {build_date} requires a newer license.")
                    return False
            
        except ValueError:
             logger.error("Invalid date format in license or build date.")
             return False
            
        logger.info(f"License Verified for {payload.get('sub')} [{payload.get('tier')}]. Updates valid until {expiry_str}.")
        return True

    except nacl.exceptions.BadSignatureError:
        logger.error("License Key Signature Verification FAILED. Tampered key?")
        return False
    except Exception as e:
        logger.error(f"License Check Error: {e}")
        return False

def is_licensed() -> bool:
    """
    Verify the Cryptographic License Key (Ed25519).
    Thread-safe implementation with optimized locking to avoid deadlocks.
    """
    global BUILD_DATE # Hint for Cython
    
    now = time.time()
    license_key_b64 = os.getenv("LICENSE_KEY", "").strip()
    key_hash = hashlib.sha256(license_key_b64.encode()).hexdigest()
    
    # 1. Fast Path: Check Cache
    with _cache_lock:
        if (_license_cache["expires"] > now and 
            _license_cache["key_hash"] == key_hash):
            return _license_cache["valid"]
    
    # 2. Security Checks (Fast)
    
    # CRITICAL SECURITY CHECK #1: BUILD_DATE injection
    if BUILD_DATE == "BUILD_DATE_PLACEHOLDER":
        logger.error("Security Error: BUILD_DATE not injected. License verification disabled.")
        with _cache_lock:
            _license_cache["valid"] = False
            _license_cache["expires"] = now + 60 # Penalty cache
            _license_cache["key_hash"] = key_hash
        return False
    
    # CRITICAL SECURITY CHECK #2: System clock manipulation
    current_date = datetime.now().date()
    if current_date < datetime(2024, 1, 1).date() or current_date > datetime(2100, 1, 1).date():
        logger.error(f"Security Error: System clock appears manipulated (date={current_date})")
        with _cache_lock:
            _license_cache["valid"] = False
            _license_cache["expires"] = now + 60
            _license_cache["key_hash"] = key_hash
        return False
    
    if not license_key_b64:
        logger.warning("No LICENSE_KEY found. Demo Mode active.")
        with _cache_lock:
            _license_cache["valid"] = False
            _license_cache["expires"] = now + 60
            _license_cache["key_hash"] = key_hash
        return False

    # 3. Slow Path: Crypto Verification (OUTSIDE LOCK)
    # This prevents the deadlock/DoS vector mentioned in the audit
    is_valid = _verify_license_crypto(license_key_b64, BUILD_DATE)

    # 4. Update Cache
    with _cache_lock:
        _license_cache["valid"] = is_valid
        _license_cache["expires"] = time.time() + 60
        _license_cache["key_hash"] = key_hash
    
    return is_valid


def obfuscare_string(text: str) -> str:
    """
    Obfuscate part of a string for Demo Mode.
    Example: "FR76 1234 5678" -> "FR76 **** ****"
    """
    if not text or len(text) < 4:
        return "****"
    
    visible = max(2, len(text) // 3)
    return text[:visible] + "*" * (len(text) - visible)
