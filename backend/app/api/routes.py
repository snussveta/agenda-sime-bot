
"""FastAPI routes for Telegram Mini App."""

import json
import logging
from typing import Any, Dict
from fastapi import APIRouter, Depends, HTTPException, status

from backend.app.database import decrypt_password, get_user, update_cached_data
from backend.app.sime import SimeAccountRole, SimeClient
from .auth import get_current_telegram_user

_LOGGER = logging.getLogger(__name__)
router = APIRouter(prefix="/api", tags=["MiniApp"])


CURRENT_CACHE_VERSION = 2


async def get_user_data(telegram_id: int, force_refresh: bool = False) -> Dict[str, Any]:
    user = await get_user(telegram_id)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not registered. Please send /start in the Telegram bot.",
        )

    cached_json = user.get("cached_data")
    if cached_json and not force_refresh:
        try:
            cached_data = json.loads(cached_json)
            # If cache has current version and absences have been checked, return it
            if cached_data.get("_v", 0) >= CURRENT_CACHE_VERSION:
                return cached_data
        except Exception:
            pass

    username = user["username"]
    password = decrypt_password(user["encrypted_password"])
    role = SimeAccountRole(user["role"])

    client = SimeClient(username=username, password=password, role=role)
    try:
        fresh = await client.fetch_data()
        fresh_dict = fresh.to_dict()
        fresh_dict["_v"] = CURRENT_CACHE_VERSION
        await update_cached_data(telegram_id, fresh_dict)
        return fresh_dict
    except Exception as e:
        _LOGGER.error("Failed to sync data for user %d: %s", telegram_id, e)
        if cached_json:
            return json.loads(cached_json)
        raise HTTPException(status_code=502, detail=f"Failed to fetch data from agenda.sime.md: {e}")
    finally:
        await client.close()


@router.get("/health")
async def health_check():
    return {"status": "ok"}


@router.get("/me")
async def get_student_profile(tg_user: dict = Depends(get_current_telegram_user)):
    data = await get_user_data(tg_user["id"])
    return {
        "student": data.get("student", {}),
        "general_average": data.get("general_average"),
        "absence_summary": data.get("absence_summary", {}),
    }


@router.get("/grades")
async def get_grades(tg_user: dict = Depends(get_current_telegram_user)):
    data = await get_user_data(tg_user["id"])
    return {
        "subjects": data.get("subjects", {}),
        "recent_grades": data.get("recent_grades", []),
        "general_average": data.get("general_average"),
    }


@router.get("/homework")
async def get_homework(tg_user: dict = Depends(get_current_telegram_user)):
    data = await get_user_data(tg_user["id"])
    return {
        "homework": data.get("homework", [])
    }


@router.get("/timetable")
async def get_timetable(tg_user: dict = Depends(get_current_telegram_user)):
    data = await get_user_data(tg_user["id"])
    return {
        "timetable": data.get("timetable", [])
    }


@router.post("/sync")
async def force_sync(tg_user: dict = Depends(get_current_telegram_user)):
    data = await get_user_data(tg_user["id"], force_refresh=True)
    return {
        "status": "synced",
        "general_average": data.get("general_average"),
        "subjects_count": len(data.get("subjects", {})),
    }
