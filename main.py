import logging
import asyncio

from aiogram import Bot, Dispatcher

from src.config.app_config import settings
from src.functionality.user.handlers import user_router
from src.functionality.base.handlers import menu_router
from src.functionality.event.handlers import event_router
from src.functionality.settings.handlers import router as settings_router

async def main():
    """The main entry point for launching a Telegram bot."""
    logging.basicConfig(level=logging.INFO)

    bot = Bot(token=settings.API_KEY)
    dp = Dispatcher()

    dp.include_router(menu_router)
    dp.include_router(user_router)
    dp.include_router(event_router)
    dp.include_router(settings_router)

    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
