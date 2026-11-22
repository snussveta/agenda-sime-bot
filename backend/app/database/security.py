"""Encryption helper for safely storing passwords."""

import base64
import hashlib
import os
from cryptography.fernet import Fernet

def get_fernet() -> Fernet:
    secret = os.getenv("SECRET_KEY", "sime-agenda-telegram-bot-default-super-secret-key-2026")
    key = base64.urlsafe_b64encode(hashlib.sha256(secret.encode()).digest())
    return Fernet(key)

def encrypt_password(password: str) -> str:
    f = get_fernet()
    return f.encrypt(password.encode()).decode()

def decrypt_password(token: str) -> str:
    f = get_fernet()
    return f.decrypt(token.encode()).decode()
