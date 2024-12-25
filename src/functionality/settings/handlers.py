from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

router = Router()

@router.message(Command("show_commands"))
async def show_commands_command(message: types.Message):
    """Показать доступные команды."""
    commands_list = (
        "/start - Start the bot\n"
        "/menu - Open the main menu\n"
        "/show_commands - View available commands\n"
        "/view_profile - View profile\n"
        "/edit_profile - Edit profile\n"
        "/create_event - Create a new event\n"
        "/view_events - View your events\n"
        "/edit_event - Edit event\n"
        "/delete_event - Delete event\n"
        "/create_team - Create a new team\n"
        "/view_teams - View your teams\n"
        "/edit_team - Edit a team\n"
        "/delete_team - Delete a team\n"
    )
    await message.answer(commands_list)

@router.message(Command("settings"))
async def settings_command(message: types.Message):
    """Команда настроек."""
    await message.answer("Settings are under development.")

@router.message(Command("empty"))
async def clear_history_command(message: types.Message, state: FSMContext):
    """Очистка состояния пользователя."""
    await state.clear()
    await message.answer("Your history has been cleared.")
