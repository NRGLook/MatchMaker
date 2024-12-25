from aiogram import Router, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.config.database_config import get_async_session
from src.models.database_models import User
from src.services.logger import LoggerProvider
from src.utils.helpers import convert_telegram_id_to_uuid
from sqlalchemy.exc import SQLAlchemyError
from src.utils.constants import WELCOME_TEXT, REGISTRATION_TEXT

user_router = Router()
logger = LoggerProvider().get_logger(__name__)


class UserStates(StatesGroup):
    FIRST_NAME = State()
    LAST_NAME = State()
    AGE = State()
    EXPERIENCE = State()


@user_router.message(Command("start"))
async def register_user(message: types.Message, state: FSMContext):
    """Start user registration."""
    print("Received /start command")
    logger.info("Processing /start command...")
    user_id = convert_telegram_id_to_uuid(message.from_user.id)
    print(f"User ID: {user_id}")

    async with get_async_session() as session:
        user = await session.get(User, user_id)
        print(f"User retrieved: {user}")
        if user and (user.first_name or user.last_name or user.age or user.experience):
            builder = InlineKeyboardBuilder()
            builder.button(text="View Profile", callback_data="view_profile")
            builder.button(text="Edit Profile", callback_data="edit_profile")
            builder.button(text="Create Event", callback_data="create_event")
            builder.button(text="View Events", callback_data="view_events")
            builder.button(text="Edit Event", callback_data="edit_event")
            builder.button(text="Delete Event", callback_data="delete_event")
            builder.button(text="Create RSVP", callback_data="create_rsvp")
            builder.button(text="View RSVP", callback_data="view_rsvp")
            builder.button(text="Edit RSVP", callback_data="edit_rsvp")
            builder.button(text="Delete RSVP", callback_data="delete_rsvp")
            builder.button(text="Create Team", callback_data="create_team")
            builder.button(text="View Teams", callback_data="view_teams")
            builder.button(text="Edit Team", callback_data="edit_team")
            builder.button(text="Delete Team", callback_data="delete_team")
            builder.button(text="Create Feedback", callback_data="create_feedback")
            builder.button(text="View Feedback", callback_data="view_feedback")
            builder.button(text="Show Commands", callback_data="show_commands")
            builder.button(text="Clear State", callback_data="clear")
            builder.button(text="Settings", callback_data="settings")

            builder.adjust(2)

            await message.answer("Choose an action:", reply_markup=builder.as_markup())
            await state.clear()
        else:
            await message.answer("Welcome! Let's start your registration. Please enter your first name:")
            await state.set_state(UserStates.FIRST_NAME)



@user_router.message(UserStates.FIRST_NAME)
async def user_first_name(message: types.Message, state: FSMContext):
    """Save user's first name and ask for the last name."""
    first_name = message.text.strip()
    await state.update_data(first_name=first_name)
    await message.answer("Enter your last name:")
    await state.set_state(UserStates.LAST_NAME)


@user_router.message(UserStates.LAST_NAME)
async def user_last_name(message: types.Message, state: FSMContext):
    """Save user's last name and ask for age."""
    last_name = message.text.strip()
    await state.update_data(last_name=last_name)
    await message.answer("Enter your age:")
    await state.set_state(UserStates.AGE)


@user_router.message(UserStates.AGE)
async def user_age(message: types.Message, state: FSMContext):
    """Save user's age and ask for experience."""
    try:
        age = int(message.text.strip())
        await state.update_data(age=age)
        await message.answer("Enter your work experience (in years):")
        await state.set_state(UserStates.EXPERIENCE)
    except ValueError:
        await message.answer("Age must be a number. Please enter a valid age.")


@user_router.message(UserStates.EXPERIENCE)
async def user_experience(message: types.Message, state: FSMContext):
    """Save user's experience and complete registration."""
    try:
        experience = int(message.text.strip())
        data = await state.get_data()
        first_name = data["first_name"]
        last_name = data["last_name"]
        age = data["age"]

        user_id = convert_telegram_id_to_uuid(message.from_user.id)

        async with get_async_session() as session:
            user = await session.get(User, user_id)
            if not user:
                user = User(
                    id=user_id,
                    username=message.from_user.username,
                    first_name=first_name,
                    last_name=last_name,
                    age=age,
                    experience=experience,
                )
                session.add(user)
            else:
                user.first_name = first_name
                user.last_name = last_name
                user.age = age
                user.experience = experience

            await session.commit()
            logger.info(f"User {user_id} registered or updated.")

        await message.answer("Registration completed successfully! You can now use the bot's features.")
        await state.clear()
    except ValueError:
        await message.answer("Experience must be a number. Please enter a valid value.")
    except SQLAlchemyError as e:
        logger.error(f"Database error during registration: {e}")
        await message.answer("An error occurred during registration. Please try again later.")


@user_router.callback_query(F.data == "edit_profile")
async def edit_user(callback: types.CallbackQuery, state: FSMContext):
    """Edit user profile."""
    await callback.message.answer("Welcome! Let's edit your registration. Please enter your first name:")
    await state.set_state(UserStates.FIRST_NAME)


@user_router.callback_query(F.data == "view_profile")
async def view_profile(callback_query: types.CallbackQuery):
    """Просмотр профиля."""
    user_id = convert_telegram_id_to_uuid(callback_query.from_user.id)

    try:
        async with get_async_session() as session:
            user = await session.get(User, user_id)
            if not user:
                await callback_query.message.edit_text("Profile not found. Please complete the registration.")
                return

            user_data = {
                "first_name": user.first_name,
                "last_name": user.last_name,
                "age": user.age,
                "experience": user.experience,
            }

            profile = (
                f"👤 Your Profile:\n"
                f"First Name: {user.first_name or 'N/A'}\n"
                f"Last Name: {user.last_name or 'N/A'}\n"
                f"Age: {user.age or 'N/A'}\n"
                f"Experience: {user.experience or 'N/A'}\n"
            )

            await callback_query.message.edit_text(profile)

    except Exception as e:
        await callback_query.message.edit_text("An error occurred while retrieving the profile.")
