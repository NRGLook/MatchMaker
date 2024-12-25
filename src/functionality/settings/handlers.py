from aiogram import Router, types, F
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext

settings_router = Router()


@settings_router.message(Command("show_commands"))
async def show_commands_command(message: types.Message):
    """Show available commands."""
    commands_list = (
        "/start - Start the bot and initialize user data\n"
        "/menu - Open the main menu with available options\n"
        "/clear - Clear the state or chat dialog of the bot\n"
        "/create_feedback - Create feedback for the Telegram bot\n"
        "/view_feedback - View your feedback and other users\n"
        "/show_commands - View all available commands\n"
        "/settings - Base settings of the bot\n"
        "/view_profile - View your profile information\n"
        "/edit_profile - Edit your profile information\n"
        "/create_event - Create a new event\n"
        "/view_events - View your created events\n"
        "/edit_event - Edit an existing event\n"
        "/delete_event - Delete an event\n"
        "/create_team - Create a new team\n"
        "/view_teams - View your teams\n"
        "/edit_team - Edit a team\n"
        "/delete_team - Delete a team\n"
    )
    await message.answer(commands_list)


@settings_router.message(Command("settings"))
async def settings_command(message: types.Message):
    """Settings team."""
    await message.answer("Settings are under development.")


@settings_router.message(Command("clear"))
async def clear_history_command(message: types.Message, state: FSMContext):
    """Clear user status and delete bot messages."""

    chat_id = message.chat.id
    clear_msg = await message.answer("Clearing your chat...")

    await message.bot.delete_message(chat_id, clear_msg.message_id)

    await state.clear()

    await message.answer("Your history has been cleared and the chat state has been reset.")


@settings_router.callback_query(F.data == "show_commands")
async def show_commands_button(callback: types.CallbackQuery):
    """Show available commands via button."""
    commands_list = (
        "/start - Start the bot and initialize user data\n"
        "/menu - Open the main menu with available options\n"
        "/clear - Clear the state or chat dialog of the bot\n"
        "/create_feedback - Create feedback for the Telegram bot\n"
        "/view_feedback - View your feedback and other users\n"
        "/show_commands - View all available commands\n"
        "/settings - Base settings of the bot\n"
        "/view_profile - View your profile information\n"
        "/edit_profile - Edit your profile information\n"
        "/create_event - Create a new event\n"
        "/view_events - View your created events\n"
        "/edit_event - Edit an existing event\n"
        "/delete_event - Delete an event\n"
        "/create_team - Create a new team\n"
        "/view_teams - View your teams\n"
        "/edit_team - Edit a team\n"
        "/delete_team - Delete a team\n"
    )
    await callback.answer()
    await callback.message.edit_text(commands_list)


@settings_router.callback_query(F.data == "settings")
async def settings_button(callback: types.CallbackQuery):
    """Settings via button."""
    await callback.answer()
    await callback.message.edit_text("Settings are under development.")


@settings_router.callback_query(F.data == "clear")
async def clear_history_button(callback: types.CallbackQuery, state: FSMContext):
    """Clear user status and delete bot messages via button."""

    chat_id = callback.message.chat.id
    clear_msg = await callback.message.answer("Clearing your chat...")

    await callback.message.bot.delete_message(chat_id, clear_msg.message_id)

    await state.clear()

    await callback.message.answer("Your history has been cleared and the chat state has been reset.")
