from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler,
    Application,
    MessageHandler,
    filters,
    ConversationHandler
)

from src.config.database_config import get_async_session
from src.models.database_models import Event, User, Category
from src.utils.helpers import convert_telegram_id_to_uuid
from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime
from telegram import Update
from telegram.ext import ContextTypes

TITLE, DATE, TIME, LOCATION, DESCRIPTION, CATEGORY, PEOPLE_AMOUNT, EXPERIENCE = range(8)

async def start_event_creation(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Start creating an event."""
    if update.message:
        await update.message.reply_text("Давайте создадим событие! Введите название события:")
    elif update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text("Давайте создадим событие! Введите название события:")

    context.user_data["field"] = "title"
    return TITLE

async def cancel_event_creation(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Cancel the event creation process."""
    await update.message.reply_text("Создание события отменено.")
    return ConversationHandler.END


def get_event_conversation_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(start_event_creation, pattern="^create_event$")],
        states={
            TITLE: [MessageHandler(filters.TEXT, handle_event_input)],
            DATE: [MessageHandler(filters.TEXT, handle_event_input)],
            TIME: [MessageHandler(filters.TEXT, handle_event_input)],
            LOCATION: [MessageHandler(filters.TEXT, handle_event_input)],
            DESCRIPTION: [MessageHandler(filters.TEXT, handle_event_input)],
            CATEGORY: [MessageHandler(filters.TEXT, handle_event_input)],
            PEOPLE_AMOUNT: [MessageHandler(filters.TEXT, handle_event_input)],
            EXPERIENCE: [MessageHandler(filters.TEXT, handle_event_input)],
        },
        fallbacks=[CommandHandler("cancel", cancel_event_creation)],
    )


async def handle_event_input(update: Update, context: ContextTypes.DEFAULT_TYPE) -> int:
    """Processing input data to create an event."""
    field = context.user_data.get("field")
    if not field:
        await update.message.reply_text("Ошибка: неизвестное поле. Попробуйте снова.")
        return TITLE

    value = update.message.text
    await update.message.reply_text(f"Получено значение: {value}. Текущий этап: {field}")

    async with get_async_session() as session:
        try:
            user_id = convert_telegram_id_to_uuid(update.effective_user.id)
            user = await session.get(User, user_id)

            if not user:
                await update.message.reply_text("Пользователь не найден. Проверьте регистрацию.")
                return ConversationHandler.END

            if field == "title":
                context.user_data["title"] = value
                context.user_data["field"] = "date"
                await update.message.reply_text("Введите дату события (в формате YYYY-MM-DD):")
                return DATE

            if field == "date":
                try:
                    context.user_data["date"] = datetime.strptime(value, '%Y-%m-%d').date()
                except ValueError:
                    await update.message.reply_text("Неверный формат даты. Попробуйте снова (YYYY-MM-DD).")
                    return DATE
                context.user_data["field"] = "time"
                await update.message.reply_text("Введите время события (в формате HH:MM):")
                return TIME

            if field == "time":
                context.user_data["time"] = value
                context.user_data["field"] = "location"
                await update.message.reply_text("Введите место проведения события:")
                return LOCATION

            if field == "location":
                context.user_data["location"] = value
                context.user_data["field"] = "description"
                await update.message.reply_text("Введите описание события:")
                return DESCRIPTION

            if field == "description":
                context.user_data["description"] = value
                context.user_data["field"] = "category"
                await update.message.reply_text("Выберите категорию события (например, Спортивное, Образовательное):")
                return CATEGORY

            if field == "category":
                result = await session.execute(select(Category).where(Category.name == value))
                category = result.scalars().first()
                if not category:
                    await update.message.reply_text("Категория не найдена. Попробуйте снова.")
                    return CATEGORY

                context.user_data["category"] = category.id
                context.user_data["field"] = "people_amount"
                await update.message.reply_text("Сколько участников будет на событии?")
                return PEOPLE_AMOUNT

            if field == "people_amount":
                try:
                    context.user_data["people_amount"] = int(value)
                except ValueError:
                    await update.message.reply_text("Введите числовое значение для количества участников.")
                    return PEOPLE_AMOUNT

                context.user_data["field"] = "experience"
                await update.message.reply_text("Какой уровень опыта требуется для участия?")
                return EXPERIENCE

            if field == "experience":
                try:
                    context.user_data["experience"] = int(value)
                except ValueError:
                    await update.message.reply_text("Введите числовое значение для уровня опыта.")
                    return EXPERIENCE

                event = Event(
                    title=context.user_data["title"],
                    date_time=datetime.combine(
                        context.user_data["date"],
                        datetime.strptime(context.user_data["time"], "%H:%M").time(),
                    ),
                    location=context.user_data["location"],
                    description=context.user_data["description"],
                    category_id=context.user_data["category"],
                    people_amount=context.user_data["people_amount"],
                    experience=context.user_data["experience"],
                    organizer_id=user_id,
                )

                session.add(event)
                await session.commit()

                await update.message.reply_text(f"Событие '{event.title}' успешно создано!")
                return ConversationHandler.END

        except SQLAlchemyError as e:
            await update.message.reply_text(f"Ошибка создания события: {e}")
            await session.rollback()

    return TITLE

async def view_events(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Просмотр всех событий, созданных пользователем."""
    user_id = convert_telegram_id_to_uuid(update.effective_user.id)
    message = update.effective_message

    if message is None:
        return

    async with get_async_session() as session:
        result = await session.execute(select(Event).where(Event.organizer_id == user_id))
        events = result.scalars().all()

        if not events:
            await message.reply_text("У вас нет созданных событий.")
            return

        events_list = "\n".join([f"Событие: {event.title} | Дата: {event.date_time}" for event in events])
        await message.reply_text(f"Ваши события:\n{events_list}")


async def edit_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Редактирование события."""
    user_id = convert_telegram_id_to_uuid(update.effective_user.id)
    event_id = context.user_data.get("event_id")

    if event_id is None:
        await update.effective_message.reply_text("ID события не найден. Выберите событие перед редактированием.")
        return

    message = update.effective_message
    if message is None:
        return

    async with get_async_session() as session:
        event = await session.get(Event, event_id)
        if not event:
            await message.reply_text("Событие не найдено.")
            return

        if event.organizer_id != user_id:
            await message.reply_text("Вы не можете редактировать это событие.")
            return

        await message.reply_text("Введите новое описание события:")
        context.user_data["field"] = "description"
        return DESCRIPTION


async def delete_event(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Удаление события."""
    user_id = convert_telegram_id_to_uuid(update.effective_user.id)
    event_id = context.user_data.get("event_id")

    if event_id is None:
        await update.effective_message.reply_text("ID события не найден. Выберите событие перед удалением.")
        return

    message = update.effective_message
    if message is None:
        return

    async with get_async_session() as session:
        event = await session.get(Event, event_id)
        if not event:
            await message.reply_text("Событие не найдено.")
            return

        if event.organizer_id != user_id:
            await message.reply_text("Вы не можете удалить это событие.")
            return

        await session.delete(event)
        await session.commit()
        await message.reply_text(f"Событие '{event.title}' было успешно удалено.")
