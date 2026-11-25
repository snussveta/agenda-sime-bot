"""Telegram bot keyboards."""

import os
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    WebAppInfo,
)

from backend.app.database import generate_user_auth_token


def build_web_app_url(telegram_id: int | None = None, base_url: str | None = None) -> str:
    raw_url = base_url or os.getenv("MINI_APP_URL", "")
    if not raw_url:
        return ""
    if not telegram_id:
        return raw_url
    token = generate_user_auth_token(telegram_id)
    sep = "&" if "?" in raw_url else "?"
    return f"{raw_url}{sep}uid={telegram_id}&token={token}"


def get_role_keyboard() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="👨‍🎓 Ученик (Elev)", callback_data="role_student"),
                InlineKeyboardButton(text="👨‍👩‍👧 Родитель (Părinte)", callback_data="role_parent"),
            ],
            [
                InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_login")
            ]
        ]
    )


def get_open_diary_inline_keyboard(telegram_id: int, mini_app_url: str | None = None) -> InlineKeyboardMarkup:
    url = build_web_app_url(telegram_id, mini_app_url)
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="📱 Открыть дневник", web_app=WebAppInfo(url=url))]
        ]
    )


def get_main_menu_keyboard(telegram_id: int | None = None, mini_app_url: str | None = None) -> ReplyKeyboardMarkup:
    url = build_web_app_url(telegram_id, mini_app_url)
    
    rows = []
    if url:
        rows.append([
            KeyboardButton(text="📱 Открыть дневник", web_app=WebAppInfo(url=url))
        ])
    
    rows.append([
        KeyboardButton(text="📊 Оценки"),
        KeyboardButton(text="📝 Домашнее задание"),
    ])
    rows.append([
        KeyboardButton(text="📅 Расписание"),
        KeyboardButton(text="🔔 Уведомления"),
    ])
    rows.append([
        KeyboardButton(text="🚪 Выйти из аккаунта")
    ])

    return ReplyKeyboardMarkup(keyboard=rows, resize_keyboard=True)


def get_cancel_keyboard() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text="❌ Отменить вход")]],
        resize_keyboard=True,
        one_time_keyboard=True,
    )
