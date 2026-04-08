from aiogram import Router
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.types import Message

router = Router()

HELP_TEXT = (
    "🏋️ *Habit Tracker*\n\n"
    "*Команды:*\n"
    "/log — заполнить привычки (сегодня или другая дата)\n"
    "/status — что уже заполнено сегодня\n"
    "/habits — список всех привычек\n"
    "/add\\_habit — добавить новую привычку\n"
    "/archive\\_habit — архивировать привычку\n"
    "/cancel — отменить текущее действие"
)


@router.message(Command("start", "help"))
async def cmd_start(message: Message) -> None:
    await message.answer(HELP_TEXT, parse_mode="Markdown")


@router.message(Command("cancel"))
async def cmd_cancel(message: Message, state: FSMContext) -> None:
    current = await state.get_state()
    await state.clear()
    if current:
        await message.answer("❌ Отменено.")
    else:
        await message.answer("Нечего отменять.")
