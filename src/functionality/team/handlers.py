from datetime import datetime

from sqlalchemy import select
from sqlalchemy.exc import SQLAlchemyError
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
from src.config.database_config import get_async_session
from src.models.database_models import Team, User
from src.services.logger import LoggerProvider
from src.utils.helpers import convert_telegram_id_to_uuid

log = LoggerProvider().get_logger(__name__)

NAME, DESCRIPTION, LOGO_URL = range(3)


async def start_team_creation(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Start creating a team."""
    if update.message:
        await update.message.reply_text("Let's create a team! Enter the team name:")
    elif update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text("Let's create a team! Enter the team name:")

    context.user_data["field"] = "name"
    return NAME

async def cancel_team_creation(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """Cancel the team creation process."""
    await update.message.reply_text("Team creation cancelled.")
    return ConversationHandler.END

async def handle_team_input(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> int:
    """Processing user input to create a team."""
    field = context.user_data.get("field")
    if not field:
        await update.message.reply_text("Error: unknown field. Please try again.")
        return NAME

    value = update.message.text
    await update.message.reply_text(f"The value received was: {value}. Current stage: {field}")

    async with get_async_session() as session:
        try:
            user_id = convert_telegram_id_to_uuid(update.effective_user.id)
            user = await session.get(User, user_id)

            if not user:
                await update.message.reply_text("User not found. Check registration.")
                return ConversationHandler.END

            if field == "name":
                context.user_data["name"] = value
                context.user_data["field"] = "description"
                await update.message.reply_text("Enter a short description of the team:")
                return DESCRIPTION

            if field == "description":
                context.user_data["description"] = value
                context.user_data["field"] = "logo_url"
                await update.message.reply_text("Enter the logo URL of the team:")
                return LOGO_URL

            if field == "logo_url":
                context.user_data["logo_url"] = value
                team = Team(
                    name=context.user_data["name"],
                    description=context.user_data["description"],
                    logo_url=context.user_data["logo_url"],
                    creator_id=user_id,
                )
                session.add(team)
                await session.commit()
                await update.message.reply_text(f"Team '{team.name}' successfully created!")
                return ConversationHandler.END

        except SQLAlchemyError as e:
            await update.message.reply_text(f"Error creating team: {e}")
            await session.rollback()

    return NAME

def get_team_conversation_handler() -> ConversationHandler:
    return ConversationHandler(
        entry_points=[CallbackQueryHandler(start_team_creation, pattern="^create_team$")],
        states={
            NAME: [MessageHandler(filters.TEXT, handle_team_input)],
            DESCRIPTION: [MessageHandler(filters.TEXT, handle_team_input)],
            LOGO_URL: [MessageHandler(filters.TEXT, handle_team_input)],
        },
        fallbacks=[CommandHandler("cancel", cancel_team_creation)],
    )

async def view_teams(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """View all teams created by the user."""
    user_id = convert_telegram_id_to_uuid(update.effective_user.id)
    message = update.effective_message

    if message is None:
        return

    async with get_async_session() as session:
        result = await session.execute(select(Team).where(Team.creator_id == user_id))
        teams = result.scalars().all()

        if not teams:
            await message.reply_text("You have no teams created.")
            return

        teams_list = "\n".join([f"Team: {team.name} | Description: {team.description}" for team in teams])
        await message.reply_text(f"Your teams:\n{teams_list}")

async def list_teams_edit(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """Lists teams for editing and immediately handles selection."""
    user_id = convert_telegram_id_to_uuid(update.effective_user.id)

    async with get_async_session() as session:
        query = select(Team.id, Team.name).where(Team.creator_id == user_id)
        result = await session.execute(query)
        teams = result.fetchall()

        if not teams:
            await update.effective_message.reply_text("You have no teams to edit.")
            return

        keyboard = [
            [InlineKeyboardButton(team.name, callback_data=f"edit_{team.id}")]
            for team in teams
        ]

        await update.effective_message.reply_text(
            "Select a team to edit:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def handle_team_edit(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """Handles editing different fields of a team."""
    query = update.callback_query
    await query.answer()

    action, team_id = query.data.split('_')
    user_id = convert_telegram_id_to_uuid(update.effective_user.id)

    async with get_async_session() as session:
        team = await session.get(Team, team_id)

        if not team or team.creator_id != user_id:
            await query.edit_message_text("Team not found or you are not the creator.")
            return

        if action == "edit":
            context.user_data['team_id'] = team_id
            context.user_data['edit_stage'] = 'name'
            await query.edit_message_text(f"Editing team '{team.name}' started. Enter the new name:")

async def list_teams_delete(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """Lists teams for deletion and immediately handles selection."""
    user_id = convert_telegram_id_to_uuid(update.effective_user.id)

    async with get_async_session() as session:
        query = select(Team.id, Team.name).where(Team.creator_id == user_id)
        result = await session.execute(query)
        teams = result.fetchall()

        if not teams:
            await update.effective_message.reply_text("You have no teams to delete.")
            return

        keyboard = [
            [InlineKeyboardButton(team.name, callback_data=f"delete_{team.id}")]
            for team in teams
        ]

        await update.effective_message.reply_text(
            "Select a team to delete:",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

async def handle_team_action(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    """Handles editing or deletion actions for a team."""
    query = update.callback_query
    await query.answer()

    action, team_id = query.data.split('_')
    user_id = convert_telegram_id_to_uuid(update.effective_user.id)

    async with get_async_session() as session:
        team = await session.get(Team, team_id)

        if not team or team.creator_id != user_id:
            await query.edit_message_text("You cannot perform this action.")
            return

        if action == "edit":
            context.user_data['team_id'] = team_id
            context.user_data['edit_stage'] = 'name'
            await query.edit_message_text(f"Editing team '{team.name}'. Please enter the new name:")

        elif action == "delete":
            await session.delete(team)
            await session.commit()
            await query.edit_message_text(f"Team '{team.name}' has been deleted.")
            return
