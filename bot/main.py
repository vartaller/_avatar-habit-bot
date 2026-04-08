import asyncio
import logging

from aiogram import Bot, Dispatcher
from aiogram.fsm.storage.memory import MemoryStorage

from bot.config import settings
from bot.middleware import OwnerOnlyMiddleware
from bot.scheduler import setup_scheduler
from bot.handlers import general, habits, log, status
from bot import database as db

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)


async def main() -> None:
    bot = Bot(token=settings.BOT_TOKEN)
    dp = Dispatcher(storage=MemoryStorage())

    # Middleware — owner-only access
    dp.message.middleware(OwnerOnlyMiddleware())
    dp.callback_query.middleware(OwnerOnlyMiddleware())

    # Routers
    dp.include_router(general.router)
    dp.include_router(log.router)
    dp.include_router(habits.router)
    dp.include_router(status.router)

    # Background scheduler (daily reminder)
    scheduler = setup_scheduler(bot)

    try:
        logging.info("Bot started")
        await dp.start_polling(bot, allowed_updates=dp.resolve_used_update_types())
    finally:
        scheduler.shutdown()
        await db.close_pool()
        await bot.session.close()
        logging.info("Bot stopped")


if __name__ == "__main__":
    asyncio.run(main())
