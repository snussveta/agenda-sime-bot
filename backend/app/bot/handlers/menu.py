"""Menu commands and button handlers."""

import json
import logging
from datetime import datetime
from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message, ReplyKeyboardRemove

from backend.app.database import (
    decrypt_password,
    delete_user,
    get_user,
    toggle_notifications,
    update_cached_data,
)
from backend.app.sime import SimeAccountRole, SimeClient
from backend.app.bot.keyboards import get_main_menu_keyboard, get_role_keyboard

_LOGGER = logging.getLogger(__name__)
router = Router(name="menu")


async def get_or_refresh_data(telegram_id: int, force: bool = False):
    user = await get_user(telegram_id)
    if not user:
        return None

    cached_json = user.get("cached_data")
    if cached_json and not force:
        try:
            return json.loads(cached_json)
        except Exception:
            pass

    username = user["username"]
    password = decrypt_password(user["encrypted_password"])
    role = SimeAccountRole(user["role"])

    client = SimeClient(username=username, password=password, role=role)
    try:
        data = await client.fetch_data()
        data_dict = data.to_dict()
        await update_cached_data(telegram_id, data_dict)
        return data_dict
    except Exception as e:
        _LOGGER.error("Failed to refresh data for %d: %s", telegram_id, e)
        if cached_json:
            return json.loads(cached_json)
        return None
    finally:
        await client.close()


@router.message(F.text == "📊 Оценки")
@router.message(Command("grades"))
async def show_grades(message: Message):
    telegram_id = message.from_user.id
    user = await get_user(telegram_id)
    if not user:
        await message.answer("⚠️ Вы не вошли в систему. Нажмите /start для входа.")
        return

    data = await get_or_refresh_data(telegram_id)
    if not data or not data.get("subjects"):
        await message.answer("⚠️ Не удалось загрузить оценки. Попробуйте позже или откройте дневник.")
        return

    subjects = data["subjects"]
    avg = data.get("general_average")

    lines = ["📊 **Ваши оценки:**\n"]
    if avg:
        lines.append(f"⭐️ **Общий средний балл: {avg}**\n")

    for subj_name, subj_info in subjects.items():
        grades = subj_info.get("grades", [])
        subj_avg = subj_info.get("average")
        sem_grade = subj_info.get("semester_grade")

        grades_str = ", ".join(str(int(g) if g.is_integer() else g) for g in grades) if grades else "нет оценок"
        avg_str = f" [средний: **{subj_avg}**]" if subj_avg else ""
        sem_str = f" [семестр: **{sem_grade}**]" if sem_grade else ""

        lines.append(f"• **{subj_name}**:{avg_str}{sem_str}\n  Оценки: `{grades_str}`")

    text = "\n".join(lines)
    if len(text) > 4000:
        for chunk in [text[i:i+3800] for i in range(0, len(text), 3800)]:
            await message.answer(chunk, parse_mode="Markdown")
    else:
        await message.answer(text, parse_mode="Markdown")


@router.message(F.text == "📝 Домашнее задание")
@router.message(Command("homework"))
async def show_homework(message: Message):
    telegram_id = message.from_user.id
    user = await get_user(telegram_id)
    if not user:
        await message.answer("⚠️ Вы не вошли в систему. Нажмите /start для входа.")
        return

    data = await get_or_refresh_data(telegram_id)
    if not data or not data.get("homework"):
        await message.answer("🎉 На ближайшие дни домашних заданий нет (или они не внесены в систему)!")
        return

    homework_list = data["homework"]
    lines = ["📝 **Домашние задания:**\n"]

    for hw in homework_list[:10]:
        due = f" (до {hw['due_date_str']})" if hw.get("due_date_str") else ""
        subj = hw.get("subject", "Предмет")
        desc = hw.get("description", "Без описания")
        lines.append(f"📌 **{subj}**{due}:\n{desc}\n")

    await message.answer("\n".join(lines), parse_mode="Markdown")


@router.message(F.text == "📅 Расписание")
@router.message(Command("timetable"))
async def show_timetable(message: Message):
    telegram_id = message.from_user.id
    user = await get_user(telegram_id)
    if not user:
        await message.answer("⚠️ Вы не вошли в систему. Нажмите /start для входа.")
        return

    data = await get_or_refresh_data(telegram_id)
    timetable = data.get("timetable", []) if data else []

    if not timetable:
        await message.answer("📅 Расписание на сегодня не найдено. Откройте дневник в приложении, чтобы посмотреть весь календарь.")
        return

    lines = ["📅 **Ближайшие уроки в расписании:**\n"]
    for lesson in timetable[:8]:
        subj = lesson.get("subject", "Урок")
        start = lesson.get("start_time", "")
        room = f", каб. {lesson['classroom']}" if lesson.get("classroom") else ""
        teacher = f" ({lesson['teacher']})" if lesson.get("teacher") else ""

        time_display = start
        if "T" in start:
            parts = start.split("T")
            time_display = f"{parts[0]} {parts[1][:5]}"

        lines.append(f"🕒 `{time_display}` — **{subj}**{room}{teacher}")

    await message.answer("\n".join(lines), parse_mode="Markdown")


@router.message(F.text == "🔔 Уведомления")
@router.message(Command("notifications"))
async def toggle_notifs(message: Message):
    telegram_id = message.from_user.id
    is_active = await toggle_notifications(telegram_id)

    status_str = "✅ **Включены**" if is_active else "❌ **Выключены**"
    await message.answer(
        f"🔔 Уведомления о новых оценках и домашних заданиях: {status_str}\n\n"
        "Когда учитель выставит оценку или добавит задание, бот пришлет вам сообщение.",
        parse_mode="Markdown",
    )


@router.message(F.text == "🚪 Выйти из аккаунта")
@router.message(Command("logout"))
async def cmd_logout(message: Message):
    telegram_id = message.from_user.id
    await delete_user(telegram_id)
    await message.answer(
        "👋 Вы вышли из своего аккаунта agenda.sime.md.\n"
        "Все сохраненные данные и сессии удалены.\n\n"
        "Чтобы войти снова, нажмите /start",
        reply_markup=ReplyKeyboardRemove(),
    )
