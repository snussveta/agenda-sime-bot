"""Async SQLite database manager."""

import json
import logging
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional
import aiosqlite

_LOGGER = logging.getLogger(__name__)

DB_PATH = Path(os.getenv("DATABASE_PATH", "./data/agenda.db"))


async def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("PRAGMA journal_mode=WAL;")
        await db.execute("""
            CREATE TABLE IF NOT EXISTS users (
                telegram_id INTEGER PRIMARY KEY,
                username TEXT NOT NULL,
                encrypted_password TEXT NOT NULL,
                role TEXT NOT NULL DEFAULT '2',
                student_name TEXT,
                school_name TEXT,
                classroom TEXT,
                notifications_enabled INTEGER DEFAULT 1,
                cached_data TEXT,
                last_synced_at TEXT,
                created_at TEXT NOT NULL,
                updated_at TEXT NOT NULL
            );
        """)
        await db.commit()
    _LOGGER.info("Database initialized at %s", DB_PATH)


async def get_user(telegram_id: int) -> Optional[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE telegram_id = ?", (telegram_id,)) as cursor:
            row = await cursor.fetchone()
            if row:
                return dict(row)
    return None


async def save_user(
    telegram_id: int,
    username: str,
    encrypted_password: str,
    role: str,
    student_name: Optional[str] = None,
    school_name: Optional[str] = None,
    classroom: Optional[str] = None,
    cached_data: Optional[Dict[str, Any]] = None,
) -> None:
    now = datetime.utcnow().isoformat()
    cached_json = json.dumps(cached_data, ensure_ascii=False) if cached_data else None

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            INSERT INTO users (
                telegram_id, username, encrypted_password, role,
                student_name, school_name, classroom,
                notifications_enabled, cached_data, last_synced_at,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, 1, ?, ?, ?, ?)
            ON CONFLICT(telegram_id) DO UPDATE SET
                username = excluded.username,
                encrypted_password = excluded.encrypted_password,
                role = excluded.role,
                student_name = coalesce(excluded.student_name, users.student_name),
                school_name = coalesce(excluded.school_name, users.school_name),
                classroom = coalesce(excluded.classroom, users.classroom),
                cached_data = coalesce(excluded.cached_data, users.cached_data),
                last_synced_at = coalesce(excluded.last_synced_at, users.last_synced_at),
                updated_at = excluded.updated_at;
        """, (
            telegram_id, username, encrypted_password, role,
            student_name, school_name, classroom,
            cached_json, now if cached_json else None, now, now
        ))
        await db.commit()


async def update_cached_data(telegram_id: int, cached_data: Dict[str, Any]) -> None:
    now = datetime.utcnow().isoformat()
    cached_json = json.dumps(cached_data, ensure_ascii=False)
    student = cached_data.get("student", {})
    name = student.get("name")
    school = student.get("school_name")
    cls = student.get("classroom")

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("""
            UPDATE users SET
                cached_data = ?,
                last_synced_at = ?,
                student_name = coalesce(?, student_name),
                school_name = coalesce(?, school_name),
                classroom = coalesce(?, classroom),
                updated_at = ?
            WHERE telegram_id = ?
        """, (cached_json, now, name, school, cls, now, telegram_id))
        await db.commit()


async def toggle_notifications(telegram_id: int) -> bool:
    user = await get_user(telegram_id)
    if not user:
        return False
    new_state = 0 if user.get("notifications_enabled", 1) == 1 else 1
    now = datetime.utcnow().isoformat()

    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute(
            "UPDATE users SET notifications_enabled = ?, updated_at = ? WHERE telegram_id = ?",
            (new_state, now, telegram_id),
        )
        await db.commit()
    return bool(new_state)


async def delete_user(telegram_id: int) -> None:
    async with aiosqlite.connect(DB_PATH) as db:
        await db.execute("DELETE FROM users WHERE telegram_id = ?", (telegram_id,))
        await db.commit()


async def get_all_active_users() -> List[Dict[str, Any]]:
    async with aiosqlite.connect(DB_PATH) as db:
        db.row_factory = aiosqlite.Row
        async with db.execute("SELECT * FROM users WHERE notifications_enabled = 1") as cursor:
            rows = await cursor.fetchall()
            return [dict(r) for r in rows]
