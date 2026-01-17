import hashlib
import sys
import os

# Import constants to ensure we use the same salt
sys.path.append(os.getcwd())
from app.constants import LICENSE_SALT

def xor_bytes(data: bytes, key: bytes) -> bytes:
    return bytes(a ^ b for a, b in zip(data, key * (len(data) // len(key) + 1)))

def main():
    if not os.path.exists("public_key.hex"):
        print("Error: public_key.hex not found.")
        sys.exit(1)
        
    with open("public_key.hex", "r") as f:
        pub_hex = f.read().strip()
        
    pub_bytes = bytes.fromhex(pub_hex)
    
    # Generate Salt Hash
    salt_hash = hashlib.sha256(LICENSE_SALT).digest()
    
    # XOR
    obfuscated = xor_bytes(pub_bytes, salt_hash)
    
    print(obfuscated.hex())

if __name__ == "__main__":
    main()
