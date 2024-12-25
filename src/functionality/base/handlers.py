from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()

@router.message(Command("menu"))
async def show_menu(message: types.Message, state: FSMContext):
    """Opening the main menu."""
    builder = InlineKeyboardBuilder()

    builder.button(text="View Profile", callback_data="view_profile")
    builder.button(text="Edit Profile", callback_data="edit_profile")
    builder.button(text="Create Event", callback_data="create_event")
    builder.button(text="View Events", callback_data="view_events")
    builder.button(text="Edit Event", callback_data="edit_event")
    builder.button(text="Delete Event", callback_data="delete_event")
    builder.button(text="Create Team", callback_data="create_team")
    builder.button(text="View Teams", callback_data="view_teams")
    builder.button(text="Edit Team", callback_data="edit_team")
    builder.button(text="Delete Team", callback_data="delete_team")
    builder.button(text="Create Feedback", callback_data="create_feedback")
    builder.button(text="View Feedback", callback_data="view_feedback")
    builder.button(text="Show Commands", callback_data="show_commands")
    builder.button(text="Clear State", callback_data="clear")
    builder.button(text="Settings", callback_data="settings")

    builder.adjust(2)

    await message.answer("Choose an action:", reply_markup=builder.as_markup())
