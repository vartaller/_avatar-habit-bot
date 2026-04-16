from datetime import date

from aiogram import Router
from aiogram.filters import Command
from aiogram.types import Message

from bot import database as db
from bot.keyboards import BOOLEAN_LABELS, TERNARY_LABELS

router = Router()


def _fmt(habit_type: str, value: int) -> str:
    if habit_type == "ternary":
        return TERNARY_LABELS.get(value, str(value))
    return BOOLEAN_LABELS.get(value, str(value))


@router.message(Command("status"))
async def cmd_status(message: Message) -> None:
    today = date.today()
    logs = await db.get_day_logs(today)
    unfilled = await db.get_unfilled_habits(today)

    lines: list[str] = [f"📊 *Status for {today.strftime('%d.%m.%Y')}*\n"]

    if logs:
        lines.append("*Filled:*")
        for log in logs:
            lines.append(f"• {log['name']}: {_fmt(log['type'], log['value'])}")

    if unfilled:
        lines.append("\n*Not filled:*")
        for h in unfilled:
            lines.append(f"• {h['name']}")

    if not logs and not unfilled:
        lines.append("No active habits. Add one: /add\\_habit")

    await message.answer("\n".join(lines), parse_mode="Markdown")
