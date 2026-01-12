import os
import hashlib
from dataclasses import dataclass

@dataclass(frozen=True)
class PasswordHash:
    salt_hex: str
    hash_hex: str

def hash_password(password: str) -> PasswordHash:
    if not password:
        raise ValueError("password kosong")
    salt = os.urandom(16)
    digest = hashlib.sha256(salt + password.encode("utf-8")).hexdigest()
    return PasswordHash(salt_hex=salt.hex(), hash_hex=digest)

def verify_password(password: str, ph: PasswordHash) -> bool:
    salt = bytes.fromhex(ph.salt_hex)
    digest = hashlib.sha256(salt + password.encode("utf-8")).hexdigest()
    return digest == ph.hash_hex