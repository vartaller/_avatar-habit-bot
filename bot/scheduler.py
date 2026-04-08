from datetime import date

from aiogram import Bot
from apscheduler.schedulers.asyncio import AsyncIOScheduler
from apscheduler.triggers.cron import CronTrigger

from bot.config import settings
from bot import database as db


async def send_reminder(bot: Bot) -> None:
    unfilled = await db.get_unfilled_habits(date.today())
    if not unfilled:
        return

    names = "\n".join(f"• {h['name']}" for h in unfilled)
    text = (
        "🔔 *Напоминание*\n\n"
        f"Сегодня ещё не заполнены:\n{names}\n\n"
        "Напиши /log чтобы заполнить."
    )
    await bot.send_message(settings.OWNER_ID, text, parse_mode="Markdown")


def setup_scheduler(bot: Bot) -> AsyncIOScheduler:
    scheduler = AsyncIOScheduler()
    scheduler.add_job(
        send_reminder,
        CronTrigger(hour=settings.REMINDER_HOUR, minute=settings.REMINDER_MINUTE),
        args=[bot],
        id="daily_reminder",
        replace_existing=True,
    )
    scheduler.start()
    return scheduler
