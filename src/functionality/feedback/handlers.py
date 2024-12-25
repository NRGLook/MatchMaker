from aiogram import Router, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder
from sqlalchemy.exc import SQLAlchemyError

from src.config.database_config import get_async_session
from src.models.database_models import Feedback, User
from src.services.logger import LoggerProvider
from src.utils.helpers import convert_telegram_id_to_uuid

from sqlalchemy import select

feedback_router = Router()
log = LoggerProvider().get_logger(__name__)


class FeedbackStates(StatesGroup):
    TEXT = State()


@feedback_router.message(Command("create_feedback"))
async def create_feedback(message: types.Message, state: FSMContext):
    """Initiate feedback creation."""
    await message.answer("Please enter your feedback:")
    await state.set_state(FeedbackStates.TEXT)


@feedback_router.callback_query(F.data == "create_feedback")
async def create_feedback(callback: types.CallbackQuery, state: FSMContext):
    """Creates a new feedback"""
    await callback.answer()
    await callback.message.edit_text(
        "Let's create a feedback! Enter the feeedback text:")
    await state.set_state(FeedbackStates.TEXT)


@feedback_router.message(FeedbackStates.TEXT)
async def save_feedback(message: types.Message, state: FSMContext):
    """Save feedback to the database."""
    feedback_text = message.text
    user_id = convert_telegram_id_to_uuid(message.from_user.id)

    async with get_async_session() as session:
        try:
            feedback = Feedback(user_id=user_id, text=feedback_text)
            session.add(feedback)
            await session.commit()
            await session.refresh(feedback)

            log.info(f"Feedback {feedback.id} created by user {user_id}")
            await message.answer("Thank you for your feedback!")
        except SQLAlchemyError as e:
            log.error(f"Failed to create feedback: {str(e)}")
            await message.answer("An error occurred while saving your feedback. Please try again later.")
        finally:
            await state.clear()


@feedback_router.callback_query(F.data == "view_feedback")
async def view_feedback(callback: types.CallbackQuery, state: FSMContext):
    """Displays all feedback."""
    await callback.answer()
    await callback.message.edit_text("Viewing all feedback:")

    async with get_async_session() as session:
        feedbacks = await session.execute(select(Feedback))
        feedbacks = feedbacks.scalars().all()

        if not feedbacks:
            await callback.message.answer("No feedback found.")
            return

        message_text = ""
        for index, feedback in enumerate(feedbacks, start=1):
            user = await session.get(User, feedback.user_id)
            username = user.username if user else "Unknown User"
            message_text += f"{index}. {username}:\n{feedback.text}\n\n"

        await callback.message.answer(message_text)

    await state.clear()
