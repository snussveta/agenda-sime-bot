"""Standalone script to test your credentials and verify agenda.sime.md connection."""

import asyncio
import os
import sys
from dotenv import load_dotenv

load_dotenv()

from backend.app.sime import SimeAccountRole, SimeClient


async def test_auth():
    username = os.getenv("TEST_SIME_USER")
    password = os.getenv("TEST_SIME_PASS")
    role_str = os.getenv("TEST_SIME_ROLE", "2")  # 1 = Parent, 2 = Student

    if not username or not password:
        print("=" * 60)
        print("🔑 ТЕСТ ПОДКЛЮЧЕНИЯ К AGENDA.SIME.MD")
        print("=" * 60)
        username = input("Введите логин (username): ").strip()
        import getpass
        password = getpass.getpass("Введите пароль: ").strip()
        role_choice = input("Роль [1 - Родитель, 2 - Ученик (по умолчанию: 2)]: ").strip()
        if role_choice == "1":
            role_str = "1"
        else:
            role_str = "2"

    role = SimeAccountRole(role_str)
    print(f"\n⏳ Авторизуемся как {'Родитель' if role == SimeAccountRole.PARENT else 'Ученик'} ({username})...")

    client = SimeClient(username=username, password=password, role=role)
    try:
        data = await client.fetch_data()
        print("\n" + "=" * 60)
        print("✅ УСПЕШНОЕ ПОДКЛЮЧЕНИЕ И ПАРСИНГ!")
        print("=" * 60)
        print(f"👤 Имя ученика: {data.student.name}")
        print(f"🏫 Школа: {data.student.school_name} ({data.student.classroom})")
        print(f"⭐️ Общий средний балл: {data.general_average}")
        print(f"📊 Количество предметов: {len(data.subjects)}")
        print(f"📝 Домашних заданий: {len(data.homework)}")
        print(f"📅 Уроков в расписании: {len(data.timetable)}")

        if data.recent_grades:
            print("\n📌 Последние оценки:")
            for g in data.recent_grades[:5]:
                print(f"   • {g.subject}: {g.grade} ({g.date_str})")

        if data.homework:
            print("\n📝 Ближайшие ДЗ:")
            for h in data.homework[:3]:
                print(f"   • [{h.subject}] {h.due_date_str}: {h.description[:60]}...")

    except Exception as e:
        print(f"\n❌ Ошибка: {e}")
    finally:
        await client.close()


if __name__ == "__main__":
    asyncio.run(test_auth())
