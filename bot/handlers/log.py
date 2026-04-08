from __future__ import annotations

from datetime import date, datetime

from aiogram import F, Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from bot import database as db
from bot.keyboards import (
    BOOLEAN_LABELS,
    TERNARY_LABELS,
    DateChoice,
    HabitSkip,
    HabitValue,
    date_choice_kb,
    habit_value_kb,
)

router = Router()


class LogFlow(StatesGroup):
    choosing_date = State()
    entering_date = State()
    logging = State()


# ── Helpers ───────────────────────────────────────────────────────────────────

def _value_label(habit_type: str, value: int) -> str:
    if habit_type == "ternary":
        return TERNARY_LABELS.get(value, str(value))
    return BOOLEAN_LABELS.get(value, str(value))


async def _start_logging(
    log_date: date,
    state: FSMContext,
    event: Message | CallbackQuery,
) -> None:
    habits = await db.get_unfilled_habits(log_date)
    date_str = log_date.strftime("%d.%m.%Y")

    if not habits:
        text = f"✅ Все привычки на {date_str} уже заполнены!"
        if isinstance(event, CallbackQuery):
            await event.message.edit_text(text)
        else:
            await event.answer(text)
        await state.clear()
        return

    await state.set_data(
        {
            "log_date": log_date.isoformat(),
            "habits": [
                {"id": str(h["id"]), "name": h["name"], "type": h["type"]}
                for h in habits
            ],
            "current_idx": 0,
        }
    )
    await state.set_state(LogFlow.logging)
    await _send_habit(state, event)


async def _send_habit(
    state: FSMContext,
    event: Message | CallbackQuery,
) -> None:
    data = await state.get_data()
    habits: list[dict] = data["habits"]
    idx: int = data["current_idx"]
    log_date = date.fromisoformat(data["log_date"])

    if idx >= len(habits):
        text = f"🎉 Готово! Все привычки на {log_date.strftime('%d.%m.%Y')} заполнены."
        if isinstance(event, CallbackQuery):
            await event.message.edit_text(text)
        else:
            await event.answer(text)
        await state.clear()
        return

    habit = habits[idx]
    text = (
        f"📋 *{habit['name']}*  ({idx + 1}/{len(habits)})\n\n"
        "Выбери значение:"
    )
    kb = habit_value_kb(habit["id"], habit["type"])

    if isinstance(event, CallbackQuery):
        await event.message.edit_text(text, reply_markup=kb, parse_mode="Markdown")
    else:
        await event.answer(text, reply_markup=kb, parse_mode="Markdown")


# ── Handlers ─────────────────────────────────────────────────────────────────

@router.message(Command("log"))
async def cmd_log(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(LogFlow.choosing_date)
    await message.answer("📅 Для какой даты заполняем?", reply_markup=date_choice_kb())


@router.callback_query(DateChoice.filter(F.action == "today"), LogFlow.choosing_date)
async def cb_today(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    await _start_logging(date.today(), state, query)


@router.callback_query(DateChoice.filter(F.action == "pick"), LogFlow.choosing_date)
async def cb_pick_date(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer()
    await state.set_state(LogFlow.entering_date)
    await query.message.edit_text("📆 Введи дату в формате *ДД.ММ.ГГГГ*:", parse_mode="Markdown")


@router.message(LogFlow.entering_date)
async def enter_date(message: Message, state: FSMContext) -> None:
    try:
        log_date = datetime.strptime(message.text.strip(), "%d.%m.%Y").date()
    except ValueError:
        await message.answer("❌ Неверный формат. Попробуй ещё раз, например *08.04.2026*:", parse_mode="Markdown")
        return
    await _start_logging(log_date, state, message)


@router.callback_query(HabitValue.filter(), LogFlow.logging)
async def cb_habit_value(
    query: CallbackQuery,
    callback_data: HabitValue,
    state: FSMContext,
) -> None:
    await query.answer()
    data = await state.get_data()
    log_date = date.fromisoformat(data["log_date"])

    await db.upsert_log(callback_data.habit_id, log_date, callback_data.value)
    await state.update_data(current_idx=data["current_idx"] + 1)
    await _send_habit(state, query)


@router.callback_query(HabitSkip.filter(), LogFlow.logging)
async def cb_habit_skip(query: CallbackQuery, state: FSMContext) -> None:
    await query.answer("Пропущено")
    data = await state.get_data()
    await state.update_data(current_idx=data["current_idx"] + 1)
    await _send_habit(state, query)
