"""Telegram WebApp initData validation."""

import hashlib
import hmac
import json
import os
import urllib.parse
from typing import Optional
from fastapi import Header, HTTPException, status

def validate_init_data(init_data: str, bot_token: str) -> dict:
    """Validate Telegram WebApp initData string using HMAC-SHA256."""
    try:
        parsed = dict(urllib.parse.parse_qsl(init_data, keep_blank_values=True))
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid initData format")

    received_hash = parsed.pop("hash", None)
    if not received_hash:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing hash in initData")

    # Construct data_check_string
    items = sorted([f"{k}={v}" for k, v in parsed.items()])
    data_check_string = "\n".join(items)

    secret_key = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    calc_hash = hmac.new(secret_key, data_check_string.encode(), hashlib.sha256).hexdigest()

    if not hmac.compare_digest(calc_hash, received_hash):
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid initData signature")

    user_raw = parsed.get("user")
    if not user_raw:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing user payload")

    try:
        user_obj = json.loads(user_raw)
        return user_obj
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user JSON in initData")


async def get_current_telegram_user(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    x_telegram_init_data: Optional[str] = Header(None, alias="X-Telegram-Init-Data"),
) -> dict:
    bot_token = os.getenv("BOT_TOKEN", "")
    
    # In development mode, allow mock user if explicitly enabled
    if os.getenv("DEV_MOCK_USER_ID") and os.getenv("DEBUG", "false").lower() == "true":
        return {"id": int(os.getenv("DEV_MOCK_USER_ID")), "first_name": "DevUser"}

    raw_data = x_telegram_init_data
    if not raw_data and authorization:
        if authorization.startswith("Bearer "):
            raw_data = authorization[7:].strip()
        elif authorization.startswith("tma "):
            raw_data = authorization[4:].strip()

    if not raw_data:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authorization header or X-Telegram-Init-Data required",
        )

    return validate_init_data(raw_data, bot_token)
