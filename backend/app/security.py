import hashlib
import secrets
from base64 import urlsafe_b64encode
from datetime import UTC, datetime, timedelta

from cryptography.fernet import Fernet
from pwdlib import PasswordHash

password_hash = PasswordHash.recommended()


def hash_password(password: str) -> str:
    return password_hash.hash(password)


def verify_password(password: str, hashed_password: str) -> bool:
    return password_hash.verify(password, hashed_password)


def create_token() -> str:
    return secrets.token_urlsafe(48)


def hash_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def encrypt_secret(secret: str, encryption_key: str, fallback_secret: str) -> str:
    key = encryption_key or urlsafe_b64encode(hashlib.sha256(fallback_secret.encode()).digest()).decode()
    return Fernet(key.encode()).encrypt(secret.encode()).decode()


def decrypt_secret(encrypted_secret: str, encryption_key: str, fallback_secret: str) -> str:
    key = encryption_key or urlsafe_b64encode(hashlib.sha256(fallback_secret.encode()).digest()).decode()
    return Fernet(key.encode()).decrypt(encrypted_secret.encode()).decode()


def expires_in(seconds: int) -> datetime:
    return datetime.now(UTC) + timedelta(seconds=seconds)
