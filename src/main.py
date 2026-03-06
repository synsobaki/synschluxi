
from __future__ import annotations

import asyncio
import logging
from typing import Any, Awaitable, Callable, Dict

from aiogram import Bot, Dispatcher
from aiogram.client.default import DefaultBotProperties
from aiogram.enums import ParseMode
from aiogram.types import TelegramObject

from sqlalchemy.ext.asyncio import AsyncSession

from src.config import load_settings
from src.infrastructure.db import init_db, async_sessionmaker
from src.app.telegram.router import setup_router
from src.app.telegram.one_screen import OneScreen
from src.app.telegram.render_service import RenderService

logging.basicConfig(level=logging.INFO)


async def db_session_middleware(
    handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
    event: TelegramObject,
    data: Dict[str, Any],
):
    sessionmaker = async_sessionmaker  # важно: это фабрика
    async with sessionmaker() as session:  # type: AsyncSession
        data["session"] = session
        try:
            result = await handler(event, data)
            await session.commit()
            return result
        except Exception:
            await session.rollback()
            raise


async def render_middleware(
    handler: Callable[[TelegramObject, Dict[str, Any]], Awaitable[Any]],
    event: TelegramObject,
    data: Dict[str, Any],
):
    bot: Bot = data["bot"]
    one_screen = OneScreen(bot)
    data["render"] = RenderService(one_screen=one_screen)
    return await handler(event, data)


async def main():
    settings = load_settings()

    bot = Bot(
        token=settings.bot_token,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )

    dp = Dispatcher()
    dp.update.middleware(db_session_middleware)
    dp.update.middleware(render_middleware)

    # твой router.py возвращает Router -> include_router тут
    router = setup_router()
    dp.include_router(router)

    await init_db()

    logging.info("🚀 Starting polling...")

    # Авто-переподключение при сетевых обрывах
    while True:
        try:
            await dp.start_polling(bot, handle_as_tasks=False)
        except (asyncio.CancelledError, KeyboardInterrupt):
            # Нормальное завершение (Ctrl+C) или отмена задач — выходим тихо
            break
        except Exception:
            logging.exception("Polling crashed, retry in 2 seconds...")
            await asyncio.sleep(2)


if __name__ == "__main__":
    asyncio.run(main())