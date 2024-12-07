from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    ContextTypes,
    ConversationHandler,
    filters,
)
from sqlalchemy.exc import SQLAlchemyError

from src.config.app_config import settings
from src.config.database_config import get_async_session
from src.models.database_models import User

import uuid

CHOOSING, TYPING, SHOW_GRID = range(3)


def convert_telegram_id_to_uuid(telegram_id: int) -> uuid.UUID:
    """Преобразует целочисленный Telegram ID в UUID."""
    return uuid.UUID(int=telegram_id, version=4)


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Стартовый обработчик: вывод кнопок выбора полей профиля."""
    keyboard = [
        [InlineKeyboardButton("Имя", callback_data="first_name"),
         InlineKeyboardButton("Фамилия", callback_data="last_name")],
        [InlineKeyboardButton("Возраст", callback_data="age"),
         InlineKeyboardButton("Опыт", callback_data="experience")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите поле для ввода информации:", reply_markup=reply_markup)
    return CHOOSING


async def button_click(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка нажатия кнопки: запоминаем выбранное поле."""
    query = update.callback_query
    await query.answer()
    context.user_data["field"] = query.data
    await query.edit_message_text(text=f"Введите значение для {query.data}:")
    return TYPING


async def handle_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Обработка ввода данных пользователем."""
    field = context.user_data.get("field")
    if not field:
        await update.message.reply_text("Ошибка: неизвестное поле.")
        return CHOOSING

    value = update.message.text

    async with get_async_session() as session:
        try:
            # Преобразуем Telegram ID в UUID
            user_id = convert_telegram_id_to_uuid(update.effective_user.id)

            # Ищем пользователя в базе
            user = await session.get(User, user_id)

            if not user:
                user = User(id=user_id, username=update.effective_user.username)
                session.add(user)

            if field in ["age", "experience"]:
                value = int(value)

            setattr(user, field, value)
            await session.commit()

            await update.message.reply_text(f"{field} успешно обновлено на {value}.")

            # Проверяем, заполнены ли все обязательные поля
            if all([user.first_name, user.last_name, user.age, user.experience]):
                await update.message.reply_text("Все поля заполнены. Переход к сетке.")
                return await show_grid(update, context)
            else:
                # Возвращаем пользователя к выбору следующего поля
                return await start(update, context)

        except (ValueError, SQLAlchemyError) as e:
            await update.message.reply_text(f"Ошибка обработки данных: {e}")
            await session.rollback()

    return CHOOSING


async def show_grid(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Отображение сетки кнопок."""
    keyboard = [
        [InlineKeyboardButton(f"Ячейка {i+1}", callback_data=f"cell_{i+1}") for i in range(4)],
        [InlineKeyboardButton(f"Ячейка {i+5}", callback_data=f"cell_{i+5}") for i in range(4)],
        [InlineKeyboardButton("Просмотреть профиль", callback_data="view_profile")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Ваши действия:", reply_markup=reply_markup)
    return SHOW_GRID


async def handle_grid_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Обработка действий на сетке."""
    query = update.callback_query
    await query.answer()

    if query.data == "view_profile":
        # Отображение профиля пользователя
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
                await query.edit_message_text(profile)
            else:
                await query.edit_message_text("Профиль не найден.")
    else:
        await query.edit_message_text(f"Вы выбрали {query.data}")


def main():
    TOKEN = settings.API_KEY

    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            CHOOSING: [CallbackQueryHandler(button_click)],
            TYPING: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_input)],
            SHOW_GRID: [CallbackQueryHandler(handle_grid_action)],
        },
        fallbacks=[],
    )

    app.add_handler(conv_handler)
    app.run_polling()


if __name__ == "__main__":
    main()
