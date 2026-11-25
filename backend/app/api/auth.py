"""Telegram WebApp initData validation and user identification."""

import hashlib
import hmac
import json
import logging
import os
import urllib.parse
from typing import Optional
from fastapi import Header, HTTPException, status
from backend.app.database import get_user

_LOGGER = logging.getLogger(__name__)


def validate_init_data(init_data: str, bot_token: str) -> dict:
    try:
        parsed = dict(urllib.parse.parse_qsl(init_data, keep_blank_values=True))
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid initData format")

    received_hash = parsed.pop("hash", None)
    if not received_hash:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Missing hash in initData")

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
        return json.loads(user_raw)
    except Exception:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid user JSON in initData")


async def get_current_telegram_user(
    authorization: Optional[str] = Header(None, alias="Authorization"),
    x_telegram_init_data: Optional[str] = Header(None, alias="X-Telegram-Init-Data"),
    x_telegram_user_id: Optional[str] = Header(None, alias="X-Telegram-User-Id"),
) -> dict:
    bot_token = os.getenv("BOT_TOKEN", "").strip().strip('"').strip("'")

    raw_data = x_telegram_init_data
    if not raw_data and authorization:
        if authorization.startswith("Bearer "):
            raw_data = authorization[7:].strip()
        elif authorization.startswith("tma "):
            raw_data = authorization[4:].strip()

    # 1. Strict Telegram HMAC validation if initData is provided
    if raw_data:
        try:
            tg_payload = validate_init_data(raw_data, bot_token)
            uid = tg_payload.get("id")
            if uid:
                user_in_db = await get_user(int(uid))
                if user_in_db:
                    return {
                        "id": int(uid),
                        "first_name": user_in_db.get("student_name", tg_payload.get("first_name", "User")),
                    }
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Вы еще не вошли в дневник. Пожалуйста, откройте бота @agenda_sime_bot и выполните вход через /start.",
                )
        except HTTPException:
            raise
        except Exception as e:
            _LOGGER.warning("Telegram initData validation error: %s", e)

    # 2. Match by X-Telegram-User-Id if user is registered in DB (fallback for webview/dev)
    if x_telegram_user_id and x_telegram_user_id.isdigit():
        uid = int(x_telegram_user_id)
        user_in_db = await get_user(uid)
        if user_in_db:
            return {"id": uid, "first_name": user_in_db.get("student_name", "User")}

    # Never fallback to another user's session!
    raise HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Требуется авторизация через Telegram. Откройте дневник через кнопку в боте @agenda_sime_bot.",
    )
