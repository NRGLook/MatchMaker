from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from sqlalchemy.exc import SQLAlchemyError

from src.config.database_config import get_async_session
from src.functionality.base.handlers import show_menu
from src.models.database_models import User
from src.functionality.user.schemes import UserSchema
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
                [InlineKeyboardButton("Пропустить ввод данных", callback_data="skip_input")],
                [InlineKeyboardButton("Редактировать профиль", callback_data="edit_profile")],
            ]
        else:
            welcome_text = REGISTRATION_TEXT
            keyboard = [
                [InlineKeyboardButton("Начать ввод данных", callback_data="start_input")],
            ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    return FIRST_NAME


async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Handle a button press to start data entry or skip."""
    query = update.callback_query
    await query.answer()

    if query.data == "start_input":
        await query.edit_message_text(text="Введите ваше имя:")
        context.user_data["field"] = "first_name"
        context.user_data["edit_mode"] = False
        return FIRST_NAME

    elif query.data == "skip_input":
        return await show_menu(update, context)

    elif query.data == "edit_profile":
        await query.edit_message_text("Редактируем профиль. Введите новое имя:")
        context.user_data["field"] = "first_name"
        context.user_data["edit_mode"] = True
        return FIRST_NAME


async def handle_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Processing user input."""
    field = context.user_data.get("field")
    if not field:
        await update.message.reply_text("Ошибка: неизвестное поле.")
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
                        f"Ошибка: поле '{field}' должно быть числом. Попробуйте снова."
                    )
                    return AGE if field == "age" else EXPERIENCE

            setattr(user, field, value)
            await session.commit()

            if field == "first_name":
                if edit_mode:
                    await update.message.reply_text("Введите новую фамилию:")
                else:
                    await update.message.reply_text("Введите вашу фамилию:")
                context.user_data["field"] = "last_name"
                return LAST_NAME

            if field == "last_name":
                if edit_mode:
                    await update.message.reply_text("Введите новый возраст:")
                else:
                    await update.message.reply_text("Введите ваш возраст:")
                context.user_data["field"] = "age"
                return AGE

            if field == "age":
                if edit_mode:
                    await update.message.reply_text("Введите новый опыт работы:")
                else:
                    await update.message.reply_text("Введите ваш опыт работы:")
                context.user_data["field"] = "experience"
                return EXPERIENCE

            if field == "experience":
                if edit_mode:
                    await update.message.reply_text("Ваш профиль обновлен. Выберите действие.")
                else:
                    await update.message.reply_text("Все данные введены. Теперь выберите действие.")
                return await show_menu(update, context)

        except (ValueError, SQLAlchemyError) as e:
            await update.message.reply_text(f"Ошибка обработки данных: {e}")
            await session.rollback()

    return FIRST_NAME
