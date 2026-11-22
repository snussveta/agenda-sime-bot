"""Background notification worker for new grades and homework."""

import asyncio
import json
import logging
from datetime import datetime
from aiogram import Bot

from ...database import (
    decrypt_password,
    get_all_active_users,
    toggle_notifications,
    update_cached_data,
)
from ...sime import SimeAccountRole, SimeAuthError, SimeClient

_LOGGER = logging.getLogger(__name__)


async def check_user_updates(bot: Bot, user: dict) -> None:
    telegram_id = user["telegram_id"]
    username = user["username"]
    role = SimeAccountRole(user["role"])

    try:
        password = decrypt_password(user["encrypted_password"])
    except Exception as e:
        _LOGGER.error("Failed to decrypt password for user %d: %s", telegram_id, e)
        return

    client = SimeClient(username=username, password=password, role=role)
    try:
        fresh_data = await client.fetch_data()
        fresh_dict = fresh_data.to_dict()

        cached_json = user.get("cached_data")
        if cached_json:
            old_dict = json.loads(cached_json)
            await notify_diff(bot, telegram_id, old_dict, fresh_dict)

        await update_cached_data(telegram_id, fresh_dict)

    except SimeAuthError:
        _LOGGER.warning("Auth failed during background check for %d. Disabling notifs.", telegram_id)
        await toggle_notifications(telegram_id)
        try:
            await bot.send_message(
                telegram_id,
                "⚠️ **Ошибка доступа к agenda.sime.md**\n"
                "Сессия устарела или пароль был изменен. Пожалуйста, выполните вход заново: /start",
                parse_mode="Markdown",
            )
        except Exception:
            pass
    except Exception as e:
        _LOGGER.warning("Background check failed for %d: %s", telegram_id, e)
    finally:
        await client.close()


async def notify_diff(bot: Bot, telegram_id: int, old_data: dict, new_data: dict) -> None:
    # 1. Compare recent grades
    old_grades = {(g["date_str"], g["subject"], float(g["grade"])) for g in old_data.get("recent_grades", [])}
    new_grades = new_data.get("recent_grades", [])

    for g in new_grades:
        key = (g["date_str"], g["subject"], float(g["grade"]))
        if key not in old_grades:
            subj_name = g["subject"]
            subj_info = new_data.get("subjects", {}).get(subj_name, {})
            avg_str = f"\n📊 Средний балл: **{subj_info.get('average')}**" if subj_info.get("average") else ""

            text = (
                "🔔 **Новая оценка в электронном дневнике!**\n\n"
                f"📚 Предмет: **{subj_name}**\n"
                f"⭐️ Оценка: **{g['grade']}**\n"
                f"📅 Дата: `{g['date_str']}`"
                f"{avg_str}"
            )
            try:
                await bot.send_message(telegram_id, text, parse_mode="Markdown")
                await asyncio.sleep(0.5)
            except Exception as err:
                _LOGGER.error("Failed to send grade notification to %d: %s", telegram_id, err)

    # 2. Compare homework
    old_hw = {(h.get("due_date_str", ""), h.get("subject", ""), h.get("description", "")) for h in old_data.get("homework", [])}
    new_hw = new_data.get("homework", [])

    for h in new_hw:
        key = (h.get("due_date_str", ""), h.get("subject", ""), h.get("description", ""))
        if key not in old_hw and h.get("description"):
            due_str = f" (до {h['due_date_str']})" if h.get("due_date_str") else ""
            text = (
                "📝 **Новое домашнее задание!**\n\n"
                f"📚 Предмет: **{h.get('subject', 'Предмет')}**{due_str}\n"
                f"📌 Задание:\n{h.get('description')}"
            )
            try:
                await bot.send_message(telegram_id, text, parse_mode="Markdown")
                await asyncio.sleep(0.5)
            except Exception as err:
                _LOGGER.error("Failed to send homework notification to %d: %s", telegram_id, err)


async def run_notification_loop(bot: Bot, interval_minutes: int = 20) -> None:
    """Continuous background loop checking for updates during active daytime hours."""
    _LOGGER.info("Starting notification background worker (interval: %d min)", interval_minutes)

    while True:
        try:
            now = datetime.now()
            # Run only between 07:30 and 20:30, Monday to Saturday
            if 7 <= now.hour <= 20 and now.weekday() <= 5:
                users = await get_all_active_users()
                for user in users:
                    await check_user_updates(bot, user)
                    await asyncio.sleep(3)  # Delay between users to avoid load spikes
        except Exception as e:
            _LOGGER.exception("Error in notification worker loop: %s", e)

        await asyncio.sleep(interval_minutes * 60)
