from datetime import datetime

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from sqlalchemy.exc import SQLAlchemyError

from src.config.database_config import get_async_session
from src.functionality.base.handlers import show_menu
from src.models.database_models import Event, User, Category
from src.utils.helpers import convert_telegram_id_to_uuid

TITLE, DATE, TIME, LOCATION, DESCRIPTION, CATEGORY, PEOPLE_AMOUNT, EXPERIENCE = range(8)


async def start_event_creation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start creating an event."""
    await update.message.reply_text("Давайте создадим событие! Введите название события:")
    context.user_data["field"] = "title"
    return TITLE


async def handle_event_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Processing input data to create an event."""
    field = context.user_data.get("field")
    if not field:
        await update.message.reply_text("Ошибка: неизвестное поле.")
        return TITLE

    value = update.message.text

    async with get_async_session() as session:
        try:
            user_id = convert_telegram_id_to_uuid(update.effective_user.id)

            user = await session.get(User, user_id)
            if not user:
                await update.message.reply_text("Пользователь не найден.")
                return TITLE

            if field == "title":
                context.user_data["title"] = value
                await update.message.reply_text("Введите дату события (в формате YYYY-MM-DD):")
                context.user_data["field"] = "date"
                return DATE

            if field == "date":
                context.user_data["date"] = datetime.strptime(value, '%Y-%m-%d').date()
                await update.message.reply_text("Введите время события (в формате HH:MM):")
                context.user_data["field"] = "time"
                return TIME

            if field == "time":
                context.user_data["time"] = value
                await update.message.reply_text("Введите место проведения события:")
                context.user_data["field"] = "location"
                return LOCATION

            if field == "location":
                context.user_data["location"] = value
                await update.message.reply_text("Введите описание события:")
                context.user_data["field"] = "description"
                return DESCRIPTION

            if field == "description":
                context.user_data["description"] = value
                await update.message.reply_text("Выберите категорию события (например, Спортивное, Образовательное):")
                context.user_data["field"] = "category"
                return CATEGORY

            if field == "category":
                category = await session.execute(f"SELECT * FROM category WHERE name='{value}'")
                category = category.scalars().first()
                if not category:
                    await update.message.reply_text("Категория не найдена, попробуйте снова.")
                    return CATEGORY
                context.user_data["category"] = category.id
                await update.message.reply_text("Сколько участников будет на событии?")
                context.user_data["field"] = "people_amount"
                return PEOPLE_AMOUNT

            if field == "people_amount":
                context.user_data["people_amount"] = int(value)
                await update.message.reply_text("Какой уровень опыта требуется для участия?")
                context.user_data["field"] = "experience"
                return EXPERIENCE

            if field == "experience":
                context.user_data["experience"] = int(value)

                title = context.user_data["title"]
                date_time = datetime.combine(context.user_data["date"], datetime.strptime(context.user_data["time"], "%H:%M").time())
                location = context.user_data["location"]
                description = context.user_data["description"]
                category_id = context.user_data["category"]
                people_amount = context.user_data["people_amount"]
                experience = context.user_data["experience"]

                event = Event(
                    title=title,
                    date_time=date_time,
                    location=location,
                    description=description,
                    category_id=category_id,
                    people_amount=people_amount,
                    experience=experience,
                    organizer_id=user_id,
                )

                session.add(event)
                await session.commit()

                await update.message.reply_text(f"Событие '{title}' успешно создано!")

                # Возвращаемся в меню
                return await show_menu(update, context)

        except SQLAlchemyError as e:
            await update.message.reply_text(f"Ошибка создания события: {e}")
            await session.rollback()

    return TITLE
