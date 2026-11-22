"""FastAPI application entry point with Aiogram bot integration."""

import asyncio
import logging
import os
from contextlib import asynccontextmanager
from pathlib import Path
from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.fsm.storage.memory import MemoryStorage
from dotenv import load_dotenv
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

load_dotenv()

from backend.app.api.routes import router as api_router
from backend.app.bot.handlers import menu, start
from backend.app.bot.notifier import run_notification_loop
from backend.app.database import init_db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
_LOGGER = logging.getLogger("agenda-app")

bot_task: asyncio.Task | None = None
notifier_task: asyncio.Task | None = None
bot_instance: Bot | None = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    global bot_task, notifier_task, bot_instance

    await init_db()

    bot_token = os.getenv("BOT_TOKEN")
    if bot_token and bot_token != "YOUR_TELEGRAM_BOT_TOKEN_HERE":
        bot_instance = Bot(
            token=bot_token,
            default=DefaultBotProperties(parse_mode=ParseMode.HTML),
        )
        dp = Dispatcher(storage=MemoryStorage())
        dp.include_router(start.router)
        dp.include_router(menu.router)

        _LOGGER.info("Starting Telegram Bot polling...")
        bot_task = asyncio.create_task(dp.start_polling(bot_instance))
        notifier_task = asyncio.create_task(run_notification_loop(bot_instance))
    else:
        _LOGGER.warning("BOT_TOKEN is not set. Bot will NOT start, only Web API is active.")

    yield

    if notifier_task:
        notifier_task.cancel()
    if bot_task:
        bot_task.cancel()
    if bot_instance:
        await bot_instance.session.close()
    _LOGGER.info("Application shutdown complete.")


app = FastAPI(
    title="Agenda SIME MD Telegram Mini App API",
    version="1.0.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 1. API routes
app.include_router(api_router)

# 2. Static Frontend files
dist_path = Path(__file__).parent.parent.parent / "frontend" / "dist"
if not dist_path.exists():
    dist_path = Path("/app/frontend/dist")

if dist_path.exists():
    _LOGGER.info("Mounting Mini App static files from %s", dist_path)
    
    # Mount assets folder so /assets/... always works
    assets_dir = dist_path / "assets"
    if assets_dir.exists():
        app.mount("/assets", StaticFiles(directory=assets_dir), name="root-assets")
        app.mount("/app/assets", StaticFiles(directory=assets_dir), name="app-assets")

    # Serve index.html for both / and /app
    @app.get("/")
    @app.get("/app")
    @app.get("/app/{full_path:path}")
    async def serve_index():
        return FileResponse(dist_path / "index.html")

    # Mount remaining root files (favicon, manifest, etc.)
    app.mount("/", StaticFiles(directory=dist_path, html=True), name="frontend")
else:
    @app.get("/")
    async def index_fallback():
        return {
            "message": "Agenda SIME MD Backend is running!",
            "note": "Frontend is not built yet. Build frontend/ or check /api/health",
        }
