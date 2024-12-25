from aiogram import Router, types
from aiogram.filters import Command
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

router = Router()

@router.message(lambda call: call.data == "menu")
async def show_menu(callback_query: types.CallbackQuery, state: FSMContext):
    """Команда для открытия меню."""
    print("Displaying menu")
    builder = InlineKeyboardBuilder()
    builder.button(text="View Profile", callback_data="view_profile")
    builder.button(text="Edit Profile", callback_data="edit_profile")
    builder.button(text="Settings", callback_data="settings")
    builder.adjust(1)

    await callback_query.message.edit_text("Choose an action:", reply_markup=builder.as_markup())
