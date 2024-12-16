from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from src.functionality.event.handlers import (
    start_event_creation,
    view_events,
    handle_event_action,
    list_events_edit,
    list_events_delete
)
from src.config.database_config import get_async_session
from src.models.database_models import User
from src.utils.helpers import convert_telegram_id_to_uuid


async def empty_commands(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Clears the bot's command list."""
    await context.bot.set_my_commands([])
    await update.message.reply_text(
        "The bot's command list has been successfully cleared. The command list is now empty."
    )


async def show_commands(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Displays available commands."""
    commands_list = (
        "/start - Start the bot\n"
        "/menu - Open the main menu\n"
        "/show_commands - View available commands\n"
        "/view_profile - View profile\n"
        "/edit_profile - Edit profile\n"
        "Cells 1-4 - Select cells for action\n"
    )

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.edit_text(f"Available commands:\n{commands_list}")
    else:
        await update.message.reply_text(f"Available commands:\n{commands_list}")


async def show_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Displays a pop-up menu with actions and buttons."""
    user_id = convert_telegram_id_to_uuid(update.effective_user.id)

    keyboard = [
        [InlineKeyboardButton("View Profile", callback_data="view_profile")],
        [InlineKeyboardButton("Edit Profile", callback_data="edit_profile")],
        [InlineKeyboardButton("Cell 1", callback_data="cell_1"),
         InlineKeyboardButton("Cell 2", callback_data="cell_2")],
        [InlineKeyboardButton("Cell 3", callback_data="cell_3"),
         InlineKeyboardButton("Cell 4", callback_data="cell_4")],
        [InlineKeyboardButton("Create Event", callback_data="create_event"),
         InlineKeyboardButton("My Events", callback_data="view_events"),
         InlineKeyboardButton("Edit Event", callback_data="edit_event"),
         InlineKeyboardButton("Delete Event", callback_data="delete_event")],
        [InlineKeyboardButton("Menu", callback_data="menu")],
        [InlineKeyboardButton("View Commands", callback_data="show_commands")],
        # [InlineKeyboardButton("Clear Bot History", callback_data="clear")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text("Choose an action:", reply_markup=reply_markup)
    elif update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text("Choose an action:", reply_markup=reply_markup)


async def handle_grid_action(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Handles actions on the grid (e.g., view profile, manage events)."""
    query = update.callback_query
    await query.answer()

    try:
        if query.data == "view_profile":
            async with get_async_session() as session:
                user_id = convert_telegram_id_to_uuid(update.effective_user.id)
                user = await session.get(User, user_id)

                if user:
                    profile = (
                        f"👤 Your Profile:\n"
                        f"First Name: {user.first_name}\n"
                        f"Last Name: {user.last_name}\n"
                        f"Age: {user.age}\n"
                        f"Experience: {user.experience}\n"
                    )
                    await query.message.edit_text(profile)
                else:
                    await query.message.edit_text("Profile not found.")

        elif query.data == "menu":
            await show_menu(update, context)

        elif query.data == "show_commands":
            await show_commands(update, context)

        elif query.data == "create_event":
            return await start_event_creation(update, context)

        elif query.data == "view_events":
            return await view_events(update, context)

        elif query.data == "edit_event":
            await list_events_edit(update, context)

        elif query.data == "delete_event":
            await list_events_delete(update, context)

        else:
            await query.message.edit_text(f"Unknown selection: {query.data}")

    except Exception as e:
        print(f"Error in handle_grid_action: {e}")
        await query.message.edit_text("An error occurred while processing your selection.")


async def cancel_action(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """Handles action cancellation (e.g., canceling event deletion/editing)."""
    query = update.callback_query
    await query.answer()

    await query.edit_message_text("Action canceled. You can return to the menu or perform another action.")

    await show_menu(update, context)
