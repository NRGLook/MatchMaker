from datetime import datetime

from aiogram import Router, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.config.database_config import get_async_session
from src.models.database_models import Event, User, Category
from src.services.logger import LoggerProvider
from src.utils.helpers import convert_telegram_id_to_uuid

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError


event_router = Router()
log = LoggerProvider().get_logger(__name__)


class EventStates(StatesGroup):
    TITLE = State()
    EDIT_TITLE = State()
    LOCATION = State()
    CATEGORY = State()
    DATE = State()
    DESCRIPTION = State()
    PEOPLE_AMOUNT = State()
    EXPERIENCE = State()


@event_router.message(Command("create_event"))
async def create_event(message: types.Message, state: FSMContext):
    """Creates a new event"""
    await message.answer(
        "Let's create an event! Enter the event title:")
    await state.update_data(change_event=False)
    await state.set_state(EventStates.TITLE)

@event_router.callback_query(F.data == "create_event")
async def create_event(callback: types.CallbackQuery, state: FSMContext):
    """Creates a new event"""
    await callback.answer()
    await callback.message.edit_text(
        "Let's create an event! Enter the event title:")
    await state.update_data(change_event=False)
    await state.set_state(EventStates.TITLE)

@event_router.message(EventStates.TITLE)
async def event_title(message: types.Message, state: FSMContext):
    """Store the event title and ask for the location."""
    title = message.text
    await state.update_data(title=title)
    await message.answer("Enter the event location:")
    await state.set_state(EventStates.LOCATION)

@event_router.message(EventStates.LOCATION)
async def event_location(message: types.Message, state: FSMContext):
    """Store the event location and ask for the category."""
    location = message.text
    await state.update_data(location=location)
    async with get_async_session() as session:
        categories = await session.execute(select(Category))
        categories = categories.scalars().all()

        builder = InlineKeyboardBuilder()

        for category in categories:
            builder.button(text=f"{category.name}", callback_data=f"{category.id}")
        builder.adjust(2)

    await message.answer("Choose the category:", reply_markup=builder.as_markup())
    await state.set_state(EventStates.CATEGORY)

@event_router.callback_query(EventStates.CATEGORY)
async def event_category(callback: types.CallbackQuery, state: FSMContext):
    """Store the event category and ask for the date and time."""
    await callback.answer()
    category_id = callback.data
    await state.update_data(category_id=category_id)
    await callback.message.answer("Enter the date and time of the event (format: DD.MM.YYYY HH:MM):")
    await state.set_state(EventStates.DATE)

@event_router.message(EventStates.DATE)
async def event_date_time(message: types.Message, state: FSMContext):
    """Store the event date and time and ask for the description."""
    try:
        date_time_str = message.text
        date_time = datetime.strptime(date_time_str, "%d.%m.%Y %H:%M")
        await state.update_data(date_time=date_time)
        await message.answer("Enter a brief description of the event:")
        await state.set_state(EventStates.DESCRIPTION)
    except ValueError:
        await message.answer("Invalid date and time format. Please use DD.MM.YYYY HH:MM")

@event_router.message(EventStates.DESCRIPTION)
async def event_description(message: types.Message, state: FSMContext):
    """Store the event description and ask for the number of people attending."""
    description = message.text
    await state.update_data(description=description)
    await message.answer("Enter the number of people attending the event:")
    await state.set_state(EventStates.PEOPLE_AMOUNT)

@event_router.message(EventStates.PEOPLE_AMOUNT)
async def event_people_amount(message: types.Message, state: FSMContext):
    """Store the number of people attending and ask for the years of experience."""
    try:
        people_amount = int(message.text)
        await state.update_data(people_amount=people_amount)
        await message.answer("Enter the years of experience required for attending the event:")
        await state.set_state(EventStates.EXPERIENCE)
    except ValueError:
        await message.answer("Invalid number of people attending or experience. Please enter a valid number.")

@event_router.message(EventStates.EXPERIENCE)
async def event_experience(message: types.Message, state: FSMContext):
    try:
        experience = int(message.text)
        data = await state.get_data()
        change_event = data.get("change_event", False)

        title = data["title"]
        location = data["location"]
        category_id = data["category_id"]
        date_time = data["date_time"]
        description = data["description"]
        people_amount = data["people_amount"]
        user_id = convert_telegram_id_to_uuid(message.from_user.id)

        async with get_async_session() as session:
            if change_event:
                event_id = data["event_id"]
                event = await session.get(Event, event_id)

                if not event:
                    await message.answer("Event not found. Please try again.")
                    return

                event.title = title
                event.location = location
                event.category_id = category_id
                event.date_time = date_time
                event.description = description
                event.people_amount = people_amount
                event.experience = experience

                await session.commit()
                await session.refresh(event)
                log.info(f"Event {event.id} updated by user {user_id}")
                await message.answer(f"Event {event.title} updated successfully!")
            else:
                event = Event(
                    title=title,
                    location=location,
                    category_id=category_id,
                    date_time=date_time,
                    description=description,
                    people_amount=people_amount,
                    experience=experience,
                    organizer_id=user_id
                )
                session.add(event)
                await session.commit()
                await session.refresh(event)
                log.info(f"Event {event.id} created by user {user_id}")
                await message.answer("Event created successfully!")

            await state.clear()

    except ValueError:
        await message.answer("Invalid experience. Please enter a valid number.")

@event_router.callback_query(F.data == "edit_event")
async def edit_event(callback: types.CallbackQuery, state: FSMContext):
    """Starts editing an existing event"""
    async with get_async_session() as session:
        user_id = convert_telegram_id_to_uuid(callback.message.chat.id)
        result = await session.execute(select(Event).where(Event.organizer_id == user_id))
        events = result.scalars().all()

        if not events:
            await callback.message.answer("You don't have any events to edit.")
            await callback.answer()

        builder = InlineKeyboardBuilder()

        for event in events:
            builder.button(text=event.title, callback_data=f"{event.id}")
        builder.adjust(2)
        await callback.message.edit_text("Choose an event to edit:", reply_markup=builder.as_markup())
        await state.set_state(EventStates.EDIT_TITLE)

@event_router.callback_query(EventStates.EDIT_TITLE)
async def edit_event_title(callback: types.CallbackQuery, state: FSMContext):
    """Store the edited event title and ask for the location."""
    await callback.answer()
    await callback.message.edit_text(
        "Let's edit an event! Enter the event title:")
    await state.update_data(change_event=True)
    await state.update_data(event_id=callback.data)
    await state.set_state(EventStates.TITLE)
