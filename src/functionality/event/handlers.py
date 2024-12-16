from sqlalchemy.ext.asyncio import AsyncSession
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
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
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


async def handle_event_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает ввод нового названия для события."""
    print("handle_event_edit: начался вызов функции")

    new_title = update.message.text
    print(f"handle_event_edit: новое название для события = {new_title}")

    event_id = context.user_data.get('event_id')
    print(f"handle_event_edit: event_id = {event_id}")

    if not event_id:
        await update.message.reply_text("Не удалось найти событие для редактирования.")
        return

    async with get_async_session() as session:
        event = await session.get(Event, event_id)

        if event:
            event.title = new_title
            await session.commit()
            await update.message.reply_text(f"Название события было успешно изменено на: {new_title}")
        else:
            await update.message.reply_text("Событие не найдено.")

        context.user_data.clear()


async def list_events_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выводит список событий для редактирования и сразу обрабатывает выбор редактирования."""
    print("list_events_edit: начался вызов функции")
    user_id = convert_telegram_id_to_uuid(update.effective_user.id)
    print(f"list_events_edit: преобразованный user_id = {user_id}")

    async with get_async_session() as session:
        query = select(Event.id, Event.title).where(Event.organizer_id == user_id)
        result = await session.execute(query)
        events = result.fetchall()

        if not events:
            await update.effective_message.reply_text("У вас нет событий для редактирования.")
            return

        print(f"list_events_edit: найдено событий: {len(events)}")

        keyboard = [
            [
                InlineKeyboardButton(event.title, callback_data=f"edit_{event.id}")
            ]
            for event in events
        ]

        print(f"list_events_edit: клавиатура: {keyboard}")

        await update.effective_message.reply_text(
            "Выберите событие для редактирования:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def list_events_delete(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Выводит список событий для удаления и сразу обрабатывает выбор удаления."""
    print("list_events_delete: начался вызов функции")
    user_id = convert_telegram_id_to_uuid(update.effective_user.id)
    print(f"list_events_delete: преобразованный user_id = {user_id}")

    async with get_async_session() as session:
        query = select(Event.id, Event.title).where(Event.organizer_id == user_id)
        result = await session.execute(query)
        events = result.fetchall()

        if not events:
            await update.effective_message.reply_text("У вас нет событий для удаления.")
            return

        print(f"list_events_delete: найдено событий: {len(events)}")

        keyboard = [
            [
                InlineKeyboardButton(event.title, callback_data=f"delete_{event.id}")
            ]
            for event in events
        ]
        await update.effective_message.reply_text(
            "Выберите событие для удаления:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def handle_event_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает действие редактирования или удаления события."""
    print("handle_event_action: начался вызов функции")

    query = update.callback_query
    await query.answer()

    try:
        action, event_id = query.data.split('_')
        print(f"handle_event_action: полученные данные: action = {action}, event_id = {event_id}")

        user_id = convert_telegram_id_to_uuid(update.effective_user.id)

        async with get_async_session() as session:
            event = await session.get(Event, event_id)

            if not event:
                await query.edit_message_text("Событие не найдено.")
                return

            if event.organizer_id != user_id:
                await query.edit_message_text("Вы не можете изменить это событие.")
                return

            if action == "edit":
                context.user_data['event_id'] = event_id
                context.user_data['edit_stage'] = 'title'
                await query.edit_message_text(
                    f"Редактирование события '{event.title}' начато. Введите новое название:"
                )

            elif action == "delete":
                await session.delete(event)
                await session.commit()
                await query.edit_message_text(f"Событие '{event.title}' было удалено.")
                return

    except Exception as e:
        print(f"Ошибка при выполнении действия: {e}")
        await query.edit_message_text("Произошла ошибка при обработке вашего выбора.")


async def handle_event_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обрабатывает редактирование различных полей события."""
    print("handle_event_edit: начался вызов функции")

    user_id = convert_telegram_id_to_uuid(update.effective_user.id)
    event_id = context.user_data.get('event_id')
    edit_stage = context.user_data.get('edit_stage')

    if not event_id:
        await update.effective_message.reply_text("Не найдено события для редактирования.")
        return

    async with get_async_session() as session:
        event = await session.get(Event, event_id)

        if not event:
            await update.effective_message.reply_text("Событие не найдено.")
            return

        if event.organizer_id != user_id:
            await update.effective_message.reply_text("Вы не можете редактировать это событие.")
            return

        if edit_stage == 'title':
            event.title = update.message.text
            context.user_data['edit_stage'] = 'description'
            await update.effective_message.reply_text(f"Название изменено на: {event.title}. Теперь введите описание:")

        elif edit_stage == 'description':
            event.description = update.message.text
            context.user_data['edit_stage'] = 'date'
            await update.effective_message.reply_text(
                f"Описание изменено на: {event.description}. Теперь введите дату:")

        elif edit_stage == 'date':
            event.date = update.message.text
            await session.commit()
            await update.effective_message.reply_text(f"Дата изменена на: {event.date}. Все изменения сохранены.")
            context.user_data.clear()
            return

        await session.commit()
