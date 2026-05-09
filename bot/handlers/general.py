from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

from bot.keyboards import main_kb

router = Router()

HELP_TEXT = (
    "🏋️ *Habit Tracker*\n\n"
    "*Commands:*\n"
    "/status — what's already filled in today\n"
    "/habits — list all habits\n"
    "/add\\_habit — add a new habit\n"
    "/archive\\_habit — archive a habit\n"
    "/cancel — cancel the current action"
)


@router.message(Command("start", "help"))
async def cmd_start(message: Message) -> None:
    await message.answer(HELP_TEXT, parse_mode="Markdown", reply_markup=main_kb())


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    current = await state.get_state()
    await state.clear()
    if current:
        await message.answer("❌ Cancelled.", reply_markup=main_kb())
    else:
        await message.answer("Nothing to cancel.", reply_markup=main_kb())
