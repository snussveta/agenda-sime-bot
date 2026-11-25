"""Start and Login handlers with FSM."""

import html
import logging
from aiogram import F, Router
from aiogram.enums import ParseMode
from aiogram.filters import Command, CommandStart
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message, ReplyKeyboardRemove

from backend.app.database import (
    delete_user,
    encrypt_password,
    get_user,
    save_user,
    update_cached_data,
)
from backend.app.sime import SimeAccountRole, SimeAuthError, SimeClient, SimeConnectionError
from backend.app.bot.keyboards import (
    get_cancel_keyboard,
    get_main_menu_keyboard,
    get_open_diary_inline_keyboard,
    get_role_keyboard,
)

_LOGGER = logging.getLogger(__name__)
router = Router(name="start")


class LoginStates(StatesGroup):
    waiting_for_role = State()
    waiting_for_username = State()
    waiting_for_password = State()


@router.message(CommandStart())
async def cmd_start(message: Message, state: FSMContext):
    await state.clear()
    telegram_id = message.from_user.id
    user = await get_user(telegram_id)

    if user and user.get("student_name"):
        name = html.escape(user.get("student_name", "Ученик"))
        school = html.escape(user.get("school_name", ""))
        classroom = html.escape(user.get("classroom", ""))
        await message.answer(
            f"👋 С возвращением, <b>{name}</b>!\n"
            f"🏫 {school} ({classroom})\n\n"
            f"Используйте кнопки меню ниже для просмотра оценок, расписания или откройте интерактивный дневник:",
            reply_markup=get_main_menu_keyboard(telegram_id),
            parse_mode=ParseMode.HTML,
        )
        return

    await message.answer(
        "👋 <b>Добро пожаловать в бота Agenda SIME MD!</b>\n\n"
        "Этот бот позволяет просматривать оценки, домашние задания, расписание уроков "
        "и получать мгновенные уведомления о новых оценках в электронном дневнике Молдовы.\n\n"
        "Чтобы начать, выберите вашу роль для входа в систему:",
        reply_markup=get_role_keyboard(),
        parse_mode=ParseMode.HTML,
    )


@router.callback_query(F.data == "cancel_login")
@router.message(F.text == "❌ Отменить вход")
async def process_cancel(event: Message | CallbackQuery, state: FSMContext):
    await state.clear()
    text = "Вход отменен. Чтобы начать заново, нажмите /start"
    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text)
        await event.answer()
    else:
        await event.answer(text, reply_markup=ReplyKeyboardRemove())


@router.callback_query(F.data.in_({"role_student", "role_parent"}))
async def process_role_selected(callback: CallbackQuery, state: FSMContext):
    role = SimeAccountRole.STUDENT if callback.data == "role_student" else SimeAccountRole.PARENT
    await state.update_data(role=role.value)
    await state.set_state(LoginStates.waiting_for_username)

    role_name = "ученика" if role == SimeAccountRole.STUDENT else "родителя"
    await callback.message.edit_text(
        f"Выбран вход для <b>{role_name}</b>.\n\n"
        "✏️ Введите ваш логин от <code>agenda.sime.md</code> (обычно первая буква имени и фамилия, например <code>i.popov</code>):",
        parse_mode=ParseMode.HTML,
    )
    await callback.answer()


@router.message(LoginStates.waiting_for_username)
async def process_username(message: Message, state: FSMContext):
    username = message.text.strip()
    if not username or len(username) < 3:
        await message.answer("⚠️ Логин слишком короткий. Пожалуйста, введите корректный логин:")
        return

    await state.update_data(username=username)
    await state.set_state(LoginStates.waiting_for_password)

    await message.answer(
        "🔑 Теперь введите ваш пароль от <code>agenda.sime.md</code>:\n\n"
        "🔒 <i>В целях безопасности ваше сообщение с паролем будет сразу же удалено из чата!</i>",
        reply_markup=get_cancel_keyboard(),
        parse_mode=ParseMode.HTML,
    )


@router.message(LoginStates.waiting_for_password)
async def process_password(message: Message, state: FSMContext):
    password = message.text.strip()
    try:
        await message.delete()
    except Exception:
        pass

    data = await state.get_data()
    username = data.get("username", "")
    role_val = data.get("role", SimeAccountRole.STUDENT.value)
    role = SimeAccountRole(role_val)
    telegram_id = message.from_user.id

    status_msg = await message.answer(
        "⏳ Проверяю данные и вхожу в <code>agenda.sime.md</code>... Пожалуйста, подождите несколько секунд.",
        reply_markup=ReplyKeyboardRemove(),
        parse_mode=ParseMode.HTML,
    )

    client = SimeClient(username=username, password=password, role=role)
    try:
        student_data = await client.fetch_data()
        student = student_data.student

        enc_pass = encrypt_password(password)
        await save_user(
            telegram_id=telegram_id,
            username=username,
            encrypted_password=enc_pass,
            role=role.value,
            student_name=student.name,
            school_name=student.school_name,
            classroom=student.classroom,
            cached_data=student_data.to_dict(),
        )

        await state.clear()
        try:
            await status_msg.delete()
        except Exception:
            pass

        avg_text = f"📊 Средний балл: <b>{student_data.general_average}</b>\n" if student_data.general_average else ""
        s_name = html.escape(student.name or "Ученик")
        s_school = html.escape(student.school_name or "Не указана")
        s_class = html.escape(student.classroom or "Не указан")

        await message.answer(
            f"🎉 <b>Успешный вход!</b>\n\n"
            f"👤 Ученик: <b>{s_name}</b>\n"
            f"🏫 Школа: <b>{s_school}</b>\n"
            f"🎒 Класс: <b>{s_class}</b>\n"
            f"{avg_text}\n"
            f"🔔 Уведомления о новых оценках: <b>Включены</b>\n\n"
            f"Теперь вы можете открыть дневник кнопкой ниже или использовать быстрое меню:",
            reply_markup=get_main_menu_keyboard(telegram_id),
            parse_mode=ParseMode.HTML,
        )

    except SimeAuthError as err:
        _LOGGER.warning("Auth error for %s: %s", username, err)
        err_text = html.escape(str(err)) or "Неверный логин или пароль."
        try:
            await status_msg.edit_text(
                f"❌ <b>Ошибка входа:</b> {err_text}\n"
                "Пожалуйста, проверьте логин и пароль и попробуйте снова: /start",
                parse_mode=ParseMode.HTML,
            )
        except Exception:
            await message.answer(f"❌ Ошибка входа: {err_text}\nПопробуйте снова: /start")
        await state.clear()
    except SimeConnectionError as err:
        _LOGGER.error("Connection error for %s: %s", username, err)
        try:
            await status_msg.edit_text(
                "⚠️ <b>Сайт agenda.sime.md временно недоступен.</b>\n"
                "Попробуйте повторить попытку через пару минут: /start",
                parse_mode=ParseMode.HTML,
            )
        except Exception:
            await message.answer("⚠️ Сайт agenda.sime.md временно недоступен. Попробуйте позже: /start")
        await state.clear()
    except Exception as err:
        _LOGGER.exception("Unexpected error during login for %s", username)
        try:
            await status_msg.edit_text(
                f"❌ Произошла ошибка: {html.escape(str(err))}\nПопробуйте снова: /start",
                parse_mode=ParseMode.HTML,
            )
        except Exception:
            await message.answer(f"❌ Произошла ошибка: {err}\nПопробуйте снова: /start")
        await state.clear()
    finally:
        await client.close()
