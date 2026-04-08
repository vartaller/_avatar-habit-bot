from __future__ import annotations

from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import State, StatesGroup
from aiogram.types import CallbackQuery, Message

from bot import database as db
from bot.keyboards import (
    ArchiveCancel,
    ArchiveConfirm,
    ArchiveSelect,
    HabitType,
    archive_confirm_kb,
    archive_list_kb,
    habit_type_kb,
)

router = Router()


class AddHabitFlow(StatesGroup):
    entering_name = State()
    choosing_type = State()


# ── Add habit ─────────────────────────────────────────────────────────────────

@router.message(Command("add_habit"))
async def cmd_add_habit(message: Message, state: FSMContext) -> None:
    await state.clear()
    await state.set_state(AddHabitFlow.entering_name)
    await message.answer("➕ Введи название новой привычки:")


@router.message(AddHabitFlow.entering_name)
async def enter_habit_name(message: Message, state: FSMContext) -> None:
    name = message.text.strip()
    if not name:
        await message.answer("Название не может быть пустым. Попробуй ещё раз:")
        return
    await state.update_data(habit_name=name)
    await state.set_state(AddHabitFlow.choosing_type)
    await message.answer(
        f"Привычка: *{name}*\n\nВыбери тип значений:",
        reply_markup=habit_type_kb(),
        parse_mode="Markdown",
    )


@router.callback_query(HabitType.filter(), AddHabitFlow.choosing_type)
async def choose_habit_type(
    query: CallbackQuery,
    callback_data: HabitType,
    state: FSMContext,
) -> None:
    await query.answer()
    data = await state.get_data()
    habit = await db.create_habit(data["habit_name"], callback_data.type)
    await state.clear()

    type_label = "🔴🟡🟢 три значения" if callback_data.type == "ternary" else "✅❌ да/нет"
    await query.message.edit_text(
        f"✅ Привычка *{habit['name']}* добавлена!\nТип: {type_label}",
        parse_mode="Markdown",
    )


# ── Archive habit ─────────────────────────────────────────────────────────────

@router.message(Command("archive_habit"))
async def cmd_archive_habit(message: Message) -> None:
    habits = await db.get_active_habits()
    if not habits:
        await message.answer("Нет активных привычек.")
        return
    await message.answer("Выбери привычку для архивации:", reply_markup=archive_list_kb(habits))


@router.callback_query(ArchiveSelect.filter())
async def archive_selected(query: CallbackQuery, callback_data: ArchiveSelect) -> None:
    await query.answer()
    habits = await db.get_all_habits()
    habit = next((h for h in habits if str(h["id"]) == callback_data.habit_id), None)
    if not habit:
        await query.message.edit_text("Привычка не найдена.")
        return
    await query.message.edit_text(
        f"Архивировать *{habit['name']}*?\n\n"
        "Данные сохранятся, но привычка пропадёт из будущих логов.",
        reply_markup=archive_confirm_kb(callback_data.habit_id),
        parse_mode="Markdown",
    )


@router.callback_query(ArchiveConfirm.filter())
async def archive_confirmed(query: CallbackQuery, callback_data: ArchiveConfirm) -> None:
    await query.answer()
    await db.archive_habit(callback_data.habit_id)
    await query.message.edit_text("🗄 Привычка архивирована.")


@router.callback_query(ArchiveCancel.filter())
async def archive_cancelled(query: CallbackQuery) -> None:
    await query.answer("Отменено")
    await query.message.edit_text("❌ Архивация отменена.")


# ── List habits ───────────────────────────────────────────────────────────────

@router.message(Command("habits"))
async def cmd_habits(message: Message) -> None:
    habits = await db.get_all_habits()
    if not habits:
        await message.answer("Привычек пока нет. Добавь первую: /add\\_habit")
        return

    active = [h for h in habits if h["is_active"]]
    archived = [h for h in habits if not h["is_active"]]

    lines: list[str] = ["📋 *Твои привычки:*\n"]

    if active:
        lines.append("*Активные:*")
        for h in active:
            emoji = "🔴🟡🟢" if h["type"] == "ternary" else "✅❌"
            lines.append(f"• {h['name']} {emoji}")

    if archived:
        lines.append("\n*Архивированные:*")
        for h in archived:
            emoji = "🔴🟡🟢" if h["type"] == "ternary" else "✅❌"
            date_str = h["archived_at"].strftime("%d.%m.%Y") if h["archived_at"] else "?"
            lines.append(f"• {h['name']} {emoji} _(с {date_str})_")

    await message.answer("\n".join(lines), parse_mode="Markdown")
