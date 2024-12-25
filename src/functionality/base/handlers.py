from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.config.app_config import settings
from src.functionality.settings.handlers import show_commands_command

menu_router = Router()


@menu_router.message(Command("menu"))
async def show_menu(
    message: types.Message,
    state: FSMContext,
):
    """Opening the main menu and managing user state."""

    user_data = await state.get_data()
    if not user_data:
        await state.update_data(opened_menu=True)

    builder = InlineKeyboardBuilder()

    builder.button(text="🔍 View Profile", callback_data="view_profile")
    builder.button(text="✏️ Edit Profile", callback_data="edit_profile")

    # builder.button(text="Create RSVP", callback_data="create_rsvp")
    # builder.button(text="View RSVP", callback_data="view_rsvp")
    # builder.button(text="Edit RSVP", callback_data="edit_rsvp")
    # builder.button(text="Delete RSVP", callback_data="delete_rsvp")

    # **Event Section**
    builder.button(text="🎉 Create Event", callback_data="create_event")
    builder.button(text="📝 View Events", callback_data="view_events")
    builder.button(text="🔧 Edit Event", callback_data="edit_event")
    builder.button(text="❌ Delete Event", callback_data="delete_event")

    # **Team Section**
    builder.button(text="👥 Create Team", callback_data="create_team")
    builder.button(text="🔎 View Teams", callback_data="view_teams")
    builder.button(text="🛠 Edit Team", callback_data="edit_team")
    builder.button(text="🗑 Delete Team", callback_data="delete_team")

    # **Feedback Section**
    builder.button(text="💬 Create Feedback", callback_data="create_feedback")
    builder.button(text="🔍 View Feedback", callback_data="view_feedback")

    # **Settings Section**
    builder.button(text="⚙️ Settings", callback_data="settings")

    # **Miscellaneous Section**
    builder.button(text="📜 Show Commands", callback_data="show_commands")
    builder.button(text="🧹 Clear State", callback_data="clear")

    builder.adjust(2)

    await message.answer("Choose an action:", reply_markup=builder.as_markup())
