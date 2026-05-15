from datetime import timedelta

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.types import Message

from bot import database as db
from bot.config import today_tz
from bot.keyboards import BOOLEAN_LABELS, BTN_VIEW, TERNARY_LABELS

router = Router()

_SEPARATOR = "\n━━━━━━━━━━━━━━━━━━━━\n"


def _fmt(habit_type: str, value: int) -> str:
    if habit_type == "ternary":
        return TERNARY_LABELS.get(value, str(value))
    return BOOLEAN_LABELS.get(value, str(value))


@router.message(Command("status"))
async def cmd_status(message: Message) -> None:
    today = today_tz()
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


@router.message(F.text == BTN_VIEW)
async def btn_view(message: Message) -> None:
    today = today_tz()
    blocks: list[str] = []

    for i in range(4):
        day = today - timedelta(days=i)
        label = day.strftime("%d.%m.%Y") + (" — today" if i == 0 else "")
        logs = await db.get_day_logs(day)

        header = f"*📅 {label}*"
        if logs:
            rows = "\n".join(f"• {r['name']}: {_fmt(r['type'], r['value'])}" for r in logs)
            blocks.append(f"{header}\n{rows}")
        else:
            blocks.append(f"{header}\n_— not filled_")

    await message.answer(_SEPARATOR.join(blocks), parse_mode="Markdown")
