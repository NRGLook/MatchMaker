import logging

from aiogram import Router, types
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from sqlalchemy.exc import SQLAlchemyError

from src.config.database_config import get_async_session
from src.functionality.base.handlers import show_menu
from src.models.database_models import User
from src.utils.constants import WELCOME_TEXT, REGISTRATION_TEXT
from src.utils.helpers import convert_telegram_id_to_uuid
from src.services.logger import LoggerProvider

router = Router()

logger = LoggerProvider().get_logger(__name__)

class UserProfileStates(StatesGroup):
    FIRST_NAME = State()
    LAST_NAME = State()
    AGE = State()
    EXPERIENCE = State()

@router.message(Command("start"))
async def start(message: types.Message, state: FSMContext):
    """Начальное приветствие с кнопками."""
    print("Received /start command")
    logger.info("Processing /start command...")
    user_id = convert_telegram_id_to_uuid(message.from_user.id)
    print(f"User ID: {user_id}")

    async with get_async_session() as session:
        user = await session.get(User, user_id)
        print(f"User retrieved: {user}")
        builder = InlineKeyboardBuilder()

        if user and (user.first_name or user.last_name or user.age or user.experience):
            welcome_text = WELCOME_TEXT
            builder.button(text="Skip data entry", callback_data="skip_input")
            builder.button(text="Edit Profile", callback_data="edit_profile")
        else:
            welcome_text = REGISTRATION_TEXT
            builder.button(text="Start data entry", callback_data="start_input")

        builder.adjust(1)

    logger.info(f"Sending welcome text: {welcome_text}")
    print(f"Welcome text: {welcome_text}")
    await message.answer(welcome_text, reply_markup=builder.as_markup())
    await state.set_state(UserProfileStates.FIRST_NAME)
    logger.info(f"State set to FIRST_NAME for user {message.from_user.id}")


@router.callback_query(StateFilter(UserProfileStates.FIRST_NAME))
async def button_click(callback_query: types.CallbackQuery, state: FSMContext):
    """Обработка нажатий на кнопки."""
    print(f"Button clicked: {callback_query.data}")
    logger.info(f"Button click: {callback_query.data}, User: {callback_query.from_user.id}")
    await callback_query.answer()

    if callback_query.data == "start_input":
        print("Starting input process")
        await callback_query.message.edit_text(text="Enter your first name:")
        await state.update_data(field="first_name", edit_mode=False)
        await state.set_state(UserProfileStates.FIRST_NAME)
        logger.info("State set to FIRST_NAME for new data entry")

    elif callback_query.data == "skip_input":
        print("Skipping input process")
        logger.info("Skipping data input, showing menu")
        await show_menu(callback_query, state)

    elif callback_query.data == "edit_profile":
        print("Editing profile")
        await callback_query.message.edit_text("Editing profile. Enter your new first name:")
        await state.update_data(field="first_name", edit_mode=True)
        await state.set_state(UserProfileStates.FIRST_NAME)
        logger.info("State set to FIRST_NAME for profile editing")

    elif callback_query.data == "view_profile":
        print("Viewing profile")
        logger.info("Viewing profile")
        await view_profile(callback_query)

    elif callback_query.data == "settings":
        print("Opening settings")
        logger.info("Opening settings")
        await settings(callback_query)

    else:
        print(f"Unknown button action: {callback_query.data}")
        await callback_query.message.edit_text("Unknown action.")

@router.message(StateFilter(UserProfileStates))
async def handle_input(message: types.Message, state: FSMContext):
    """Обработка пользовательского ввода."""
    print(f"Handling user input: {message.text}")
    data = await state.get_data()
    print(f"State data: {data}")
    field = data.get("field")
    edit_mode = data.get("edit_mode", False)

    if not field:
        print("Error: unknown field")
        await message.answer("Error: unknown field.")
        return

    value = message.text

    async with get_async_session() as session:
        try:
            user_id = convert_telegram_id_to_uuid(message.from_user.id)
            user = await session.get(User, user_id)
            print(f"User fetched: {user}")

            if not user:
                print("Creating new user")
                user = User(id=user_id, username=message.from_user.username)
                session.add(user)

            if field in ("age", "experience"):
                try:
                    value = int(value)
                except ValueError:
                    print(f"Invalid input for field {field}: {value}")
                    await message.answer(f"Error: the '{field}' field must be a number. Please try again.")
                    await show_menu(callback_query=None, message=message, state=state)
                    return

            setattr(user, field, value)
            print(f"Updated user field {field}: {value}")
            await session.commit()

            next_field = None
            if field == "first_name":
                next_field = "last_name"
                await message.answer("Enter your new last name:" if edit_mode else "Enter your last name:")
            elif field == "last_name":
                next_field = "age"
                await message.answer("Enter your new age:" if edit_mode else "Enter your age:")
            elif field == "age":
                next_field = "experience"
                await message.answer("Enter your new work experience:" if edit_mode else "Enter your work experience:")
            elif field == "experience":
                await message.answer(
                    "Your profile has been updated. Choose an action." if edit_mode else "All data has been entered. Now choose an action."
                )
                await show_menu(callback_query=None, message=message, state=state)

            if next_field:
                await state.update_data(field=next_field)
                print(f"Next field set to {next_field}")
                await getattr(UserProfileStates, next_field.upper()).set()

        except (ValueError, SQLAlchemyError) as e:
            print(f"Error processing data: {e}")
            await message.answer(f"Error processing data: {e}")
            await session.rollback()

@router.callback_query(lambda call: call.data == "view_profile")
async def view_profile(callback_query: types.CallbackQuery):
    print("View profile clicked")
    logger.info(f"view_profile triggered by user {callback_query.from_user.id}")

    try:
        async with get_async_session() as session:
            user_id = convert_telegram_id_to_uuid(callback_query.from_user.id)
            print(f"Converted User ID: {user_id}")
            user = await session.get(User, user_id)
            print(f"Fetched user: {user}")

            if not user:
                logger.warning(f"User {user_id} not found")
                await callback_query.message.edit_text("Profile not found. Please complete the registration.")
                return

            user_data = {
                "first_name": user.first_name,
                "last_name": user.last_name,
                "age": user.age,
                "experience": user.experience,
            }
            print(f"User data: {user_data}")

            profile = (
                f"👤 Your Profile:\n"
                f"First Name: {user.first_name or 'N/A'}\n"
                f"Last Name: {user.last_name or 'N/A'}\n"
                f"Age: {user.age or 'N/A'}\n"
                f"Experience: {user.experience or 'N/A'}\n"
            )
            print(f"Profile content: {profile}")

            await callback_query.message.edit_text(profile)
            print("Profile displayed successfully")
            logger.info(f"Profile displayed for user {user_id}")

    except Exception as e:
        print(f"Error in view_profile: {e}")
        logger.error(f"Error in view_profile: {e}")
        await callback_query.message.edit_text("An error occurred while retrieving the profile.")
