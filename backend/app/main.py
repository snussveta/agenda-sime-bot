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

# Load environment variables
load_dotenv()

from .api.routes import router as api_router
from .bot.handlers import menu, start
from .bot.notifier import run_notification_loop
from .database import init_db

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

    # 1. Initialize SQLite Database
    await init_db()

    # 2. Setup Aiogram Bot if token is configured
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

    # Shutdown
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

# CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include API routes
app.include_router(api_router)

# Mount Static Frontend
dist_path = Path(__file__).parent.parent.parent / "frontend" / "dist"
if not dist_path.exists():
    # If inside docker container
    dist_path = Path("/app/frontend/dist")

if dist_path.exists():
    _LOGGER.info("Mounting Mini App static files from %s", dist_path)
    app.mount("/app", StaticFiles(directory=dist_path, html=True), name="frontend")

    @app.get("/")
    async def index_redirect():
        return FileResponse(dist_path / "index.html")
else:
    @app.get("/")
    async def index_fallback():
        return {
            "message": "Agenda SIME MD Backend is running!",
            "note": "Frontend is not built yet. Build frontend/ or check /api/health",
        }
