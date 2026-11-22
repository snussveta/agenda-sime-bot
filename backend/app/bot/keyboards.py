"""Telegram bot keyboards."""

import os
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
    WebAppInfo,
)


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


def get_main_menu_keyboard(mini_app_url: str | None = None) -> ReplyKeyboardMarkup:
    url = mini_app_url or os.getenv("MINI_APP_URL", "")
    
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
