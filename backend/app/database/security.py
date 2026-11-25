"""Encryption helper for safely storing passwords."""

import base64
import hashlib
import hmac
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

def generate_user_auth_token(telegram_id: int) -> str:
    secret = os.getenv("SECRET_KEY", "sime-agenda-telegram-bot-default-super-secret-key-2026")
    msg = f"agenda_user_{telegram_id}"
    return hmac.new(secret.encode(), msg.encode(), hashlib.sha256).hexdigest()

def verify_user_auth_token(telegram_id: int, token: str) -> bool:
    if not token or not telegram_id:
        return False
    expected = generate_user_auth_token(telegram_id)
    return hmac.compare_digest(expected, token)
