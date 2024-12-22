from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from sqlalchemy.exc import SQLAlchemyError

from src.config.database_config import get_async_session
from src.functionality.base.handlers import show_menu
from src.models.database_models import User
from src.utils.constants import WELCOME_TEXT, REGISTRATION_TEXT
from src.utils.helpers import convert_telegram_id_to_uuid


FIRST_NAME, LAST_NAME, AGE, EXPERIENCE, VIEW_PROFILE, EDIT_PROFILE = range(6)


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """The initial welcome window with a button to start entering data."""
    user_id = convert_telegram_id_to_uuid(update.effective_user.id)

    async with get_async_session() as session:
        user = await session.get(User, user_id)
        if user and (user.first_name or user.last_name or user.age or user.experience):
            welcome_text = WELCOME_TEXT
            keyboard = [
                [InlineKeyboardButton("Skip data entry", callback_data="skip_input")],
                [InlineKeyboardButton("Edit Profile", callback_data="edit_profile")],
            ]
        else:
            welcome_text = REGISTRATION_TEXT
            keyboard = [
                [InlineKeyboardButton("Start data entry", callback_data="start_input")],
            ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    return FIRST_NAME


async def button_click(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Handle a button press to start data entry or skip."""
    query = update.callback_query
    await query.answer()

    if query.data == "start_input":
        await query.edit_message_text(text="Enter your first name:")
        context.user_data["field"] = "first_name"
        context.user_data["edit_mode"] = False
        return FIRST_NAME

    elif query.data == "skip_input":
        return await show_menu(update, context)

    elif query.data == "edit_profile":
        await query.edit_message_text("Editing profile. Enter your new first name:")
        context.user_data["field"] = "first_name"
        context.user_data["edit_mode"] = True
        return FIRST_NAME


async def handle_input(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Processing user input."""
    field = context.user_data.get("field")
    if not field:
        await update.message.reply_text("Error: unknown field.")
        return FIRST_NAME

    value = update.message.text
    edit_mode = context.user_data.get("edit_mode", False)

    async with get_async_session() as session:
        try:
            user_id = convert_telegram_id_to_uuid(update.effective_user.id)
            user = await session.get(User, user_id)

            if not user:
                user = User(id=user_id, username=update.effective_user.username)
                session.add(user)

            if field in ("age", "experience"):
                try:
                    value = int(value)
                except ValueError:
                    await update.message.reply_text(
                        f"Error: the '{field}' field must be a number. Please try again."
                    )
                    return AGE if field == "age" else EXPERIENCE

            setattr(user, field, value)
            await session.commit()

            if field == "first_name":
                if edit_mode:
                    await update.message.reply_text("Enter your new last name:")
                else:
                    await update.message.reply_text("Enter your last name:")
                context.user_data["field"] = "last_name"
                return LAST_NAME

            if field == "last_name":
                if edit_mode:
                    await update.message.reply_text("Enter your new age:")
                else:
                    await update.message.reply_text("Enter your age:")
                context.user_data["field"] = "age"
                return AGE

            if field == "age":
                if edit_mode:
                    await update.message.reply_text("Enter your new work experience:")
                else:
                    await update.message.reply_text("Enter your work experience:")
                context.user_data["field"] = "experience"
                return EXPERIENCE

            if field == "experience":
                if edit_mode:
                    await update.message.reply_text("Your profile has been updated. Choose an action.")
                else:
                    await update.message.reply_text("All data has been entered. Now choose an action.")
                return await show_menu(update, context)

        except (ValueError, SQLAlchemyError) as e:
            await update.message.reply_text(f"Error processing data: {e}")
            await session.rollback()

    return FIRST_NAME
