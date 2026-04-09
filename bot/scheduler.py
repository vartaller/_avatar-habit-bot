import logging
from datetime import date

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from bot.config import settings
from bot import database as db

logger = logging.getLogger(__name__)


async def send_reminder(bot: Bot) -> None:
    try:
        unfilled = await db.get_unfilled_habits(date.today())
    except Exception:
        logger.exception("send_reminder: failed to fetch unfilled habits")
        return

    if not unfilled:
        return

    names = "\n".join(f"• {h['name']}" for h in unfilled)
    text = (
        "🔔 *Напоминание*\n\n"
        f"Сегодня ещё не заполнены:\n{names}\n\n"
        "Напиши /log чтобы заполнить."
    )
    try:
        await bot.send_message(settings.OWNER_ID, text, parse_mode="Markdown")
    except Exception:
        logger.exception("send_reminder: failed to send message")


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler(timezone=settings.TIMEZONE)
    scheduler.add_job(
        send_reminder,
        CronTrigger(
            hour=settings.REMINDER_HOUR,
            minute=settings.REMINDER_MINUTE,
            timezone=settings.TIMEZONE,
        ),
        args=[bot],
        id="daily_reminder",
        replace_existing=True,
    )
    scheduler.start()
    return scheduler
