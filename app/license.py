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
from datetime import datetime, timezone
import nacl.signing
import nacl.encoding
import nacl.exceptions
from typing import Optional, Dict

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
_license_cache = {"valid": None, "payload": None, "expires": 0, "key_hash": None}
_cache_lock = threading.Lock()


def _verify_license_crypto(license_key_b64: str) -> Optional[Dict]:
    """Verify Ed25519 signed license payload and return payload dict if valid."""
    try:
        verify_key_hex = _deobfuscate_key()
        verify_key = nacl.signing.VerifyKey(verify_key_hex, encoder=nacl.encoding.HexEncoder)
        
        try:
            signed_data = base64.b64decode(license_key_b64, validate=True)
        except Exception:
            logger.error("License Key is not valid Base64.")
            return None

        # Verify signature and extract payload
        try:
            payload_bytes = verify_key.verify(signed_data)
        except nacl.exceptions.BadSignatureError:
            logger.error("License signature verification FAILED: Invalid signature.")
            return None
            
        payload = json.loads(payload_bytes.decode('utf-8'))
        
        # Validate required fields
        required_fields = ["sub", "exp", "tier"]
        if not all(field in payload for field in required_fields):
            logger.error(f"License payload missing fields: {[f for f in required_fields if f not in payload]}")
            return None
            
        # Check expiry
        expiry_str = payload.get("exp")
        try:
            # Flexible date parsing: try ISO format first, fallback to YYYY-MM-DD
            try:
                expiry_date = datetime.fromisoformat(expiry_str.replace('Z', '+00:00'))
            except ValueError:
                expiry_date = datetime.strptime(expiry_str, "%Y-%m-%d")
                # Make naive datetime timezone-aware (assume UTC)
                expiry_date = expiry_date.replace(tzinfo=timezone.utc)
                
            now_utc = datetime.now(timezone.utc)    
            if now_utc > expiry_date:
                logger.warning(f"License EXPIRED on {expiry_str}. Features disabled.")
                return None
            
            # Warn if expiring soon (within 7 days)
            days_remaining = (expiry_date - now_utc).days
            if days_remaining <= 7:
                logger.warning(f"⚠️  License expires in {days_remaining} days (on {expiry_str})!")
                
        except ValueError as e:
            logger.error(f"Invalid date format in license: {e}")
            return None
            
        logger.info(f"✅ License verified: {payload.get('sub')} [{payload.get('tier')}] valid until {expiry_str}")
        return payload

    except nacl.exceptions.BadSignatureError:
        logger.error("License signature verification FAILED.")
        return None
    except Exception as e:
        logger.error(f"License check error: {e}")
        return None


def get_license_payload() -> Optional[Dict]:
    """
    Get the verified license payload.
    Thread-safe with caching for performance.
    """
    now = time.time()
    license_key_b64 = os.getenv("LICENSE_KEY", "").strip()
    key_hash = hashlib.sha256(license_key_b64.encode()).hexdigest()
    
    # Fast path: check cache
    with _cache_lock:
        if (_license_cache["expires"] > now and 
            _license_cache["key_hash"] == key_hash):
            return _license_cache["payload"] if _license_cache["valid"] else None
    
    # No license key = Community mode
    if not license_key_b64:
        with _cache_lock:
            _license_cache["valid"] = False
            _license_cache["payload"] = None
            _license_cache["expires"] = now + 60  # Cache for 1 min
            _license_cache["key_hash"] = key_hash
        return None

    # Verify license (slow path)
    payload = _verify_license_crypto(license_key_b64)
    is_valid = payload is not None

    # Update cache
    with _cache_lock:
        _license_cache["valid"] = is_valid
        _license_cache["payload"] = payload
        _license_cache["expires"] = now + 60  # Cache for 1 min
        _license_cache["key_hash"] = key_hash
    
    return payload


def is_licensed() -> bool:
    """Backward compatibility wrapper: check if any valid license is present."""
    return get_license_payload() is not None

def has_tier(required_tiers: list[str]) -> bool:
    """Check if the current license is within the accepted tiers."""
    payload = get_license_payload()
    if not payload:
        return False
    return payload.get("tier", "").lower() in [t.lower() for t in required_tiers]
