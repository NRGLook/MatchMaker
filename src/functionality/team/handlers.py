from datetime import datetime

from aiogram import Router, types, F
from aiogram.filters import Command, StateFilter
from aiogram.fsm.state import State, StatesGroup
from aiogram.fsm.context import FSMContext
from aiogram.utils.keyboard import InlineKeyboardBuilder

from src.config.database_config import get_async_session
from src.models.database_models import Team, User
from src.services.logger import LoggerProvider
from src.utils.helpers import convert_telegram_id_to_uuid

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError

team_router = Router()
log = LoggerProvider().get_logger(__name__)


class TeamStates(StatesGroup):
    NAME = State()
    EDIT_NAME = State()
    DELETE_TEAM = State()
    DESCRIPTION = State()
    LOGO_URL = State()


@team_router.message(Command("create_team"))
async def create_team_command(message: types.Message, state: FSMContext):
    """Creates a new team via command."""
    await message.answer(
        "Let's create a team! Enter the team's name:")
    await state.update_data(change_team=False)
    await state.set_state(TeamStates.NAME)


@team_router.callback_query(F.data == "create_team")
async def create_team_callback(callback: types.CallbackQuery, state: FSMContext):
    """Creates a new team via callback."""
    await callback.answer()
    await callback.message.edit_text(
        "Let's create a team! Enter the team's name:")
    await state.update_data(change_team=False)
    await state.set_state(TeamStates.NAME)


@team_router.message(TeamStates.NAME)
async def team_name(message: types.Message, state: FSMContext):
    """Store the team's name and ask for the description."""
    name = message.text
    await state.update_data(name=name)
    await message.answer("Enter a short description of the team:")
    await state.set_state(TeamStates.DESCRIPTION)


@team_router.message(TeamStates.DESCRIPTION)
async def team_description(message: types.Message, state: FSMContext):
    """Store the team's description and ask for the logo URL."""
    description = message.text
    await state.update_data(description=description)
    await message.answer("Enter the URL of the team's logo:")
    await state.set_state(TeamStates.LOGO_URL)


@team_router.message(TeamStates.LOGO_URL)
async def team_logo_url(message: types.Message, state: FSMContext):
    """Store the team's logo URL and finalize the creation or update."""
    logo_url = message.text
    await state.update_data(logo_url=logo_url)

    data = await state.get_data()
    change_team = data.get("change_team", False)

    name = data["name"]
    description = data["description"]
    user_id = convert_telegram_id_to_uuid(message.from_user.id)

    try:
        async with get_async_session() as session:
            if change_team:
                team_id = data["team_id"]
                team = await session.get(Team, team_id)

                if not team:
                    await message.answer("Team not found. Please try again.")
                    return

                team.name = name
                team.description = description
                team.logo_url = logo_url

                await session.commit()
                await session.refresh(team)
                log.info(f"Team {team.id} updated by user {user_id}")
                await message.answer(f"Team {team.name} updated successfully!")
            else:
                team = Team(
                    name=name,
                    description=description,
                    logo_url=logo_url,
                    creator_id=user_id
                )
                session.add(team)
                await session.commit()
                await session.refresh(team)
                log.info(f"Team {team.id} created by user {user_id}")
                await message.answer("Team created successfully!")

            await state.clear()

    except SQLAlchemyError as e:
        log.error(f"Database error: {e}")
        await message.answer("An error occurred while saving the team. Please try again.")


@team_router.callback_query(F.data == "edit_team")
async def edit_my_team(callback: types.CallbackQuery, state: FSMContext):
    """Starts editing an existing team."""
    async with get_async_session() as session:
        user_id = convert_telegram_id_to_uuid(callback.message.chat.id)
        result = await session.execute(select(Team).where(Team.creator_id == user_id))
        teams = result.scalars().all()

        if not teams:
            await callback.message.answer("You don't have any teams to edit.")
            await callback.answer()
            return

        builder = InlineKeyboardBuilder()

        for team in teams:
            builder.button(text=team.name, callback_data=f"{team.id}")
        builder.adjust(2)
        await callback.message.edit_text("Choose a team to edit:", reply_markup=builder.as_markup())
        await state.set_state(TeamStates.EDIT_NAME)


@team_router.callback_query(TeamStates.EDIT_NAME)
async def edit_team_name(callback: types.CallbackQuery, state: FSMContext):
    """Store the edited team's name."""
    await callback.answer()
    await callback.message.edit_text("Let's edit a team! Enter the team's name:")
    await state.update_data(change_team=True)
    await state.update_data(team_id=callback.data)
    await state.set_state(TeamStates.NAME)


@team_router.callback_query(F.data == "delete_team")
async def delete_my_team(callback: types.CallbackQuery, state: FSMContext):
    """Starts deleting an existing team."""
    async with get_async_session() as session:
        user_id = convert_telegram_id_to_uuid(callback.message.chat.id)
        result = await session.execute(select(Team).where(Team.creator_id == user_id))
        teams = result.scalars().all()

        if not teams:
            await callback.message.answer("You don't have any teams to delete.")
            await callback.answer()
            return

        builder = InlineKeyboardBuilder()

        for team in teams:
            builder.button(text=team.name, callback_data=f"{team.id}")
        builder.adjust(2)
        await callback.message.edit_text("Choose a team to delete:", reply_markup=builder.as_markup())
        await state.set_state(TeamStates.DELETE_TEAM)


@team_router.callback_query(TeamStates.DELETE_TEAM)
async def delete_team(callback: types.CallbackQuery, state: FSMContext):
    """Confirm the deletion of the team."""
    await callback.answer()
    team_id = callback.data

    async with get_async_session() as session:
        team = await session.get(Team, team_id)
        if team:
            await session.delete(team)
            await session.commit()
            log.info(f"Team {team_id} deleted by user {convert_telegram_id_to_uuid(callback.message.chat.id)}")
            await callback.message.edit_text("Team deleted successfully!")
            await state.clear()
        else:
            await callback.message.edit_text("Team not found. Please try again.")


@team_router.callback_query(F.data == "view_teams")
async def view_teams(callback: types.CallbackQuery, state: FSMContext):
    """Starts viewing all teams."""
    await callback.answer()
    await callback.message.edit_text("Viewing all teams:")
    async with get_async_session() as session:
        teams = await session.execute(select(Team))
        teams = teams.scalars().all()
        message_text = ""
        if not teams:
            await callback.message.answer("No teams found.")
        else:
            for index, team in enumerate(teams, start=1):
                message_text += f"{index}. {team.name}\n{team.description}\n\n"
            await callback.message.answer(message_text)
        await state.clear()
