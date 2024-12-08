from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from sqlalchemy.exc import SQLAlchemyError

from src.config.database_config import get_async_session
from src.models.database_models import User
from src.functionality.user.schemes import UserSchema
from src.utils.helpers import convert_telegram_id_to_uuid


FIRST_NAME, LAST_NAME, AGE, EXPERIENCE, SHOW_GRID, VIEW_PROFILE, EDIT_PROFILE = range(7)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Стартовое приветственное окно с кнопкой начала ввода данных."""
    user_id = convert_telegram_id_to_uuid(update.effective_user.id)

    async with get_async_session() as session:
        user = await session.get(User, user_id)
        if user and (user.first_name or user.last_name or user.age or user.experience):
            welcome_text = (
                "Привет! Ты уже заполнил часть данных. Хотите обновить информацию или пропустить шаги?"
            )
            keyboard = [
                [InlineKeyboardButton("Пропустить ввод данных", callback_data="skip_input")],
                [InlineKeyboardButton("Редактировать профиль", callback_data="edit_profile")],
            ]
        else:
            welcome_text = (
                "Привет! Я помогу тебе создать профиль.\n"
                "Для начала, давай введем несколько данных.\n"
                "Нажми кнопку ниже, чтобы начать!"
            )
            keyboard = [
                [InlineKeyboardButton("Начать ввод данных", callback_data="start_input")],
            ]

    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text(welcome_text, reply_markup=reply_markup)
    return FIRST_NAME


async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка нажатия кнопки для начала ввода данных или пропуска."""
    query = update.callback_query
    await query.answer()

    if query.data == "start_input":
        await query.edit_message_text(text="Введите ваше имя:")
        context.user_data["field"] = "first_name"
        return FIRST_NAME

    elif query.data == "skip_input":
        return await show_grid(update, context)

    elif query.data == "edit_profile":
        return await show_grid(update, context)


async def handle_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка ввода данных пользователем."""
    field = context.user_data.get("field")
    if not field:
        await update.message.reply_text("Ошибка: неизвестное поле.")
        return FIRST_NAME

    value = update.message.text

    async with get_async_session() as session:
        try:
            user_id = convert_telegram_id_to_uuid(update.effective_user.id)

            user = await session.get(User, user_id)

            if not user:
                user = User(id=user_id, username=update.effective_user.username)
                session.add(user)

            user_data = {field: value}
            validated_data = UserSchema(**user_data)

            setattr(user, field, validated_data.dict()[field])
            await session.commit()

            if field == "first_name":
                await update.message.reply_text("Введите вашу фамилию:")
                context.user_data["field"] = "last_name"
                return LAST_NAME

            if field == "last_name":
                await update.message.reply_text("Введите ваш возраст:")
                context.user_data["field"] = "age"
                return AGE

            if field == "age":
                await update.message.reply_text("Введите ваш опыт работы:")
                context.user_data["field"] = "experience"
                return EXPERIENCE

            if field == "experience":
                await update.message.reply_text("Все данные введены. Теперь выберите действие.")
                return await show_grid(update, context)

        except (ValueError, SQLAlchemyError) as e:
            await update.message.reply_text(f"Ошибка обработки данных: {e}")
            await session.rollback()

    return FIRST_NAME


async def show_grid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отображение сетки кнопок после ввода данных или при нажатии на 'Меню'."""
    query = update.callback_query
    await query.answer()

    keyboard = [
        [InlineKeyboardButton(f"Ячейка {i+1}", callback_data=f"cell_{i+1}") for i in range(4)],
        [InlineKeyboardButton(f"Ячейка {i+5}", callback_data=f"cell_{i+5}") for i in range(4)],
        [InlineKeyboardButton("Просмотреть профиль", callback_data="view_profile"),
         InlineKeyboardButton("Меню", callback_data="menu")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await query.message.reply_text("Ваши действия:", reply_markup=reply_markup)
    return SHOW_GRID


async def handle_grid_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка действий на сетке (например, просмотр профиля и возврат в меню)."""
    query = update.callback_query
    await query.answer()

    if query.data == "view_profile":
        async with get_async_session() as session:
            user_id = convert_telegram_id_to_uuid(update.effective_user.id)
            user = await session.get(User, user_id)

            if user:
                profile = (
                    f"👤 Ваш профиль:\n"
                    f"Имя: {user.first_name}\n"
                    f"Фамилия: {user.last_name}\n"
                    f"Возраст: {user.age}\n"
                    f"Опыт: {user.experience}\n"
                )
                await query.message.edit_text(profile)
            else:
                await query.message.edit_text("Профиль не найден.")
    elif query.data == "menu":
        await query.message.edit_text("Меню:\n1. Просмотреть профиль\n2. Редактировать профиль")
        await query.message.reply_text(
            "Выберите, что хотите сделать: \n"
            "1. Просмотр профиля\n"
            "2. Редактирование профиля"
        )
        return SHOW_GRID
    else:
        await query.message.edit_text(f"Вы выбрали {query.data}")
