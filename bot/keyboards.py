from datetime import date, timedelta

from aiogram.filters.callback_data import CallbackData
from aiogram.types import (
    InlineKeyboardButton,
    InlineKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardMarkup,
)
from aiogram.utils.keyboard import InlineKeyboardBuilder

# ── Constants ─────────────────────────────────────────────────────────────────

BTN_LOG = "📝 Log"

# ── Value labels ─────────────────────────────────────────────────────────────

TERNARY_LABELS: dict[int, str] = {
    0: "🟢 OK / Not at all",
    1: "🟡 A bit",
    2: "🔴 A lot / Very much",
}

BOOLEAN_LABELS: dict[int, str] = {
    1: "✅ Done",
    0: "❌ Missed",
}


# ── Callback data ─────────────────────────────────────────────────────────────

class DateChoice(CallbackData, prefix="date"):
    date_str: str  # ISO date e.g. "2026-05-09"


class HabitValue(CallbackData, prefix="hval"):
    habit_id: str
    value: int


class HabitSkip(CallbackData, prefix="hskip"):
    habit_id: str


class HabitType(CallbackData, prefix="htype"):
    type: str  # "ternary" | "boolean"


class ArchiveSelect(CallbackData, prefix="arch_sel"):
    habit_id: str


class ArchiveConfirm(CallbackData, prefix="arch_ok"):
    habit_id: str


class ArchiveCancel(CallbackData, prefix="arch_no"):
    pass


# ── Keyboards ─────────────────────────────────────────────────────────────────

def main_kb() -> ReplyKeyboardMarkup:
    return ReplyKeyboardMarkup(
        keyboard=[[KeyboardButton(text=BTN_LOG)]],
        resize_keyboard=True,
    )


def date_choice_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    today = date.today()
    for i in range(4):
        d = today - timedelta(days=i)
        label = d.strftime("%d.%m") + (" (today)" if i == 0 else "")
        builder.button(
            text=f"{'📅' if i == 0 else '📆'} {label}",
            callback_data=DateChoice(date_str=d.isoformat()),
        )
    builder.adjust(2)
    return builder.as_markup()


def habit_value_kb(habit_id: str, habit_type: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    if habit_type == "ternary":
        for val, label in TERNARY_LABELS.items():
            builder.button(text=label, callback_data=HabitValue(habit_id=habit_id, value=val))
        builder.adjust(1)
    else:
        for val, label in BOOLEAN_LABELS.items():
            builder.button(text=label, callback_data=HabitValue(habit_id=habit_id, value=val))
        builder.adjust(2)
    builder.row(
        InlineKeyboardButton(text="⏭ Skip", callback_data=HabitSkip(habit_id=habit_id).pack())
    )
    return builder.as_markup()


def habit_type_kb() -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="🔴🟡🟢 Three values (ternary)", callback_data=HabitType(type="ternary"))
    builder.button(text="✅❌ Yes / No (boolean)", callback_data=HabitType(type="boolean"))
    builder.adjust(1)
    return builder.as_markup()


def archive_list_kb(habits: list[dict]) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    for h in habits:
        builder.button(
            text=f"🗄 {h['name']}",
            callback_data=ArchiveSelect(habit_id=str(h["id"])),
        )
    builder.adjust(1)
    return builder.as_markup()


def archive_confirm_kb(habit_id: str) -> InlineKeyboardMarkup:
    builder = InlineKeyboardBuilder()
    builder.button(text="✅ Yes, archive", callback_data=ArchiveConfirm(habit_id=habit_id))
    builder.button(text="❌ Cancel", callback_data=ArchiveCancel())
    builder.adjust(2)
    return builder.as_markup()
