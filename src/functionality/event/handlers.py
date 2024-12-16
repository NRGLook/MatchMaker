from datetime import datetime

from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes
from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler,
    MessageHandler,
    filters,
    ConversationHandler
)

from src.config.database_config import get_async_session
from src.models.database_models import Event, User, Category
from src.services.logger import LoggerProvider
from src.utils.helpers import convert_telegram_id_to_uuid

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

log = LoggerProvider().get_logger(__name__)

TITLE, DATE, TIME, LOCATION, DESCRIPTION, CATEGORY, PEOPLE_AMOUNT, EXPERIENCE = range(8)


async def start_event_creation(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Start creating an event."""
    if update.message:
        await update.message.reply_text("Let's create an event! Enter the event name:")
    elif update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text("Let's create an event! Enter the event name:")

    context.user_data["field"] = "title"

    return TITLE


async def cancel_event_creation(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """Cancel the event creation process."""
    await update.message.reply_text("Event creation cancelled.")
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


async def handle_event_input(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Processing input data to create an event."""
    field = context.user_data.get("field")
    if not field:
        await update.message.reply_text("Error: unknown field. Please try again.")
        return TITLE

    value = update.message.text
    await update.message.reply_text(f"The value received was: {value}. Current stage: {field}")

    async with get_async_session() as session:
        try:
            user_id = convert_telegram_id_to_uuid(update.effective_user.id)
            user = await session.get(User, user_id)

            if not user:
                await update.message.reply_text("User not found. Check registration.")
                return ConversationHandler.END

            if field == "title":
                context.user_data["title"] = value
                context.user_data["field"] = "date"
                await update.message.reply_text("Enter the date of the event (in YYYY-MM-DD format):")
                return DATE

            if field == "date":
                try:
                    context.user_data["date"] = datetime.strptime(value, '%Y-%m-%d').date()
                except ValueError:
                    await update.message.reply_text("Invalid date format. Try again (YYYY-MM-DD).")
                    return DATE
                context.user_data["field"] = "time"
                await update.message.reply_text("Enter the event time (in HH:MM format):")
                return TIME

            if field == "time":
                context.user_data["time"] = value
                context.user_data["field"] = "location"
                await update.message.reply_text("Enter the location of the event:")
                return LOCATION

            if field == "location":
                context.user_data["location"] = value
                context.user_data["field"] = "description"
                await update.message.reply_text("Enter event description:")
                return DESCRIPTION

            if field == "description":
                context.user_data["description"] = value
                context.user_data["field"] = "category"
                await update.message.reply_text("Select an event category (e.g. Sports, Education):")
                return CATEGORY

            if field == "category":
                result = await session.execute(select(Category).where(Category.name == value))
                category = result.scalars().first()
                if not category:
                    categories = await session.execute(select(Category))
                    category_list = categories.scalars().all()
                    category_names = ", ".join([cat.name for cat in category_list])

                    await update.message.reply_text(
                        f"Category not found. Please select one of the existing categories: {category_names} или введите новую."
                    )
                    return CATEGORY

                context.user_data["category"] = category.id
                context.user_data["field"] = "people_amount"
                await update.message.reply_text("How many participants will there be at the event?")
                return PEOPLE_AMOUNT

            if field == "people_amount":
                try:
                    context.user_data["people_amount"] = int(value)
                except ValueError:
                    await update.message.reply_text("Enter a numeric value for the number of participants.")
                    return PEOPLE_AMOUNT

                context.user_data["field"] = "experience"
                await update.message.reply_text("What level of experience is required to participate?")
                return EXPERIENCE

            if field == "experience":
                try:
                    context.user_data["experience"] = int(value)
                except ValueError:
                    await update.message.reply_text("Enter a numeric value for the experience level.")
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

                await update.message.reply_text(f"Event '{event.title}' successfully created!")
                return ConversationHandler.END

        except SQLAlchemyError as e:
            await update.message.reply_text(f"Error creating event: {e}")
            await session.rollback()

    return TITLE

async def view_events(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """View all events created by the user."""
    user_id = convert_telegram_id_to_uuid(update.effective_user.id)
    message = update.effective_message

    if message is None:
        return

    async with get_async_session() as session:
        result = await session.execute(select(Event).where(Event.organizer_id == user_id))
        events = result.scalars().all()

        if not events:
            await message.reply_text("You have no events created.")
            return

        events_list = "\n".join([f"Event: {event.title} | Date: {event.date_time}" for event in events])
        await message.reply_text(f"Your events:\n{events_list}")


async def handle_event_edit(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """Handles input of a new title for an event."""
    log.info("handle_event_edit: function call started")

    new_title = update.message.text
    log.info(f"handle_event_edit: new title for the event = {new_title}")

    event_id = context.user_data.get('event_id')
    log.info(f"handle_event_edit: event_id = {event_id}")

    if not event_id:
        await update.message.reply_text("Could not find the event for editing.")
        return

    async with get_async_session() as session:
        event = await session.get(Event, event_id)

        if event:
            event.title = new_title
            await session.commit()
            await update.message.reply_text(f"Event title has been successfully updated to: {new_title}")
        else:
            await update.message.reply_text("Event not found.")

        context.user_data.clear()


async def list_events_edit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Lists events for editing and immediately handles selection."""
    log.info("list_events_edit: function call started")
    user_id = convert_telegram_id_to_uuid(update.effective_user.id)
    log.info(f"list_events_edit: converted user_id = {user_id}")

    async with get_async_session() as session:
        query = select(Event.id, Event.title).where(Event.organizer_id == user_id)
        result = await session.execute(query)
        events = result.fetchall()

        if not events:
            await update.effective_message.reply_text("You have no events to edit.")
            return

        log.info(f"list_events_edit: number of events found: {len(events)}")

        keyboard = [
            [
                InlineKeyboardButton(event.title, callback_data=f"edit_{event.id}")
            ]
            for event in events
        ]

        log.info(f"list_events_edit: keyboard: {keyboard}")

        await update.effective_message.reply_text(
            "Select an event to edit:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def list_events_delete(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """Lists events for deletion and immediately handles selection."""
    log.info("list_events_delete: function call started")
    user_id = convert_telegram_id_to_uuid(update.effective_user.id)
    log.info(f"list_events_delete: converted user_id = {user_id}")

    async with get_async_session() as session:
        query = select(Event.id, Event.title).where(Event.organizer_id == user_id)
        result = await session.execute(query)
        events = result.fetchall()

        if not events:
            await update.effective_message.reply_text("You have no events to delete.")
            return

        log.info(f"list_events_delete: number of events found: {len(events)}")

        keyboard = [
            [
                InlineKeyboardButton(event.title, callback_data=f"delete_{event.id}")
            ]
            for event in events
        ]
        await update.effective_message.reply_text(
            "Select an event to delete:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )


async def handle_event_action(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """Handles editing or deletion actions for an event."""
    log.info("handle_event_action: function call started")

    query = update.callback_query
    await query.answer()

    try:
        action, event_id = query.data.split('_')
        log.info(f"handle_event_action: received data: action = {action}, event_id = {event_id}")

        user_id = convert_telegram_id_to_uuid(update.effective_user.id)

        async with get_async_session() as session:
            event = await session.get(Event, event_id)

            if not event:
                await query.edit_message_text("Event not found.")
                return

            if event.organizer_id != user_id:
                await query.edit_message_text("You cannot edit this event.")
                return

            if action == "edit":
                context.user_data['event_id'] = event_id
                context.user_data['edit_stage'] = 'title'
                await query.edit_message_text(
                    f"Editing event '{event.title}' started. Please enter a new title:"
                )

            elif action == "delete":
                await session.delete(event)
                await session.commit()
                await query.edit_message_text(f"Event '{event.title}' has been deleted.")
                return

    except Exception as e:
        log.info(f"Error while performing the action: {e}")
        await query.edit_message_text("An error occurred while processing your selection.")


async def handle_event_edit(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """Handles editing different fields of an event."""
    log.info("handle_event_edit: function call started")

    user_id = convert_telegram_id_to_uuid(update.effective_user.id)
    event_id = context.user_data.get('event_id')
    edit_stage = context.user_data.get('edit_stage')

    if not event_id:
        await update.effective_message.reply_text("No event found for editing.")
        return

    async with get_async_session() as session:
        event = await session.get(Event, event_id)

        if not event:
            await update.effective_message.reply_text("Event not found.")
            return

        if event.organizer_id != user_id:
            await update.effective_message.reply_text("You cannot edit this event.")
            return

        if edit_stage == 'title':
            event.title = update.message.text
            context.user_data['edit_stage'] = 'description'
            await update.effective_message.reply_text(f"Title updated to: {event.title}. Now enter the description:")

        elif edit_stage == 'description':
            event.description = update.message.text
            context.user_data['edit_stage'] = 'date'
            await update.effective_message.reply_text(
                f"Description updated to: {event.description}. Now enter the date:")

        elif edit_stage == 'date':

            try:
                new_date = datetime.strptime(update.message.text, "%Y-%m-%d").date()

                log.info(f"Attempting to save the date: {new_date}")

                event.date_time = new_date

                session.add(event)

                log.info(f"Date before commit (event.date_time): {event.date_time}")

                await session.commit()

                updated_event = await session.get(Event, event_id)

                if updated_event and updated_event.date_time == new_date:
                    await update.effective_message.reply_text(
                        f"Date updated to: {new_date}. All changes saved."
                    )
                    log.info(f"Date successfully saved: {updated_event.date_time}")

                else:
                    await update.effective_message.reply_text(
                        "An error occurred while saving the date."
                    )
                    log.info(
                        f"Date not updated in the database. Expected: {new_date}, "
                        f"Received: {updated_event.date_time if updated_event else 'None'}"
                    )

            except ValueError as e:
                await update.effective_message.reply_text(
                    "Invalid date format. Please use the YYYY-MM-DD format."
                )
                log.info(f"Date conversion error: {e}")
                return
            except Exception as e:
                await update.effective_message.reply_text(
                    f"An error occurred while saving: {str(e)}"
                )
                log.info(f"Unknown error: {e}")
                return
            context.user_data.clear()

            return

        await session.commit()
