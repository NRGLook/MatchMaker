from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import ContextTypes

from src.functionality.event.handlers import (
    start_event_creation,
    view_events,
    handle_event_action,
    list_events_edit,
    list_events_delete
)
from src.config.database_config import get_async_session
from src.models.database_models import User
from src.utils.helpers import convert_telegram_id_to_uuid


async def empty_commands(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Clears the bot's command list."""
    await context.bot.set_my_commands([])
    await update.message.reply_text(
        "Команды бота успешно очищены. Список команд теперь пуст."
    )


async def show_commands(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Displays available commands."""
    commands_list = (
        "/start - Запуск бота\n"
        "/menu - Открытие главного меню\n"
        "/show_commands - Просмотр доступных команд\n"
        "/view_profile - Просмотр профиля\n"
        "/edit_profile - Редактирование профиля\n"
        "Ячейки 1-4 - Выбор ячеек для действия\n"
    )

    if update.callback_query:
        await update.callback_query.answer()
        await update.callback_query.message.edit_text(f"Доступные команды:\n{commands_list}")
    else:
        await update.message.reply_text(f"Доступные команды:\n{commands_list}")


async def show_menu(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    """Display a pop-up menu with actions and buttons."""
    user_id = convert_telegram_id_to_uuid(update.effective_user.id)

    keyboard = [
        [InlineKeyboardButton("Просмотреть профиль", callback_data="view_profile")],
        [InlineKeyboardButton("Редактировать профиль", callback_data="edit_profile")],
        [InlineKeyboardButton(f"Ячейка 1", callback_data="cell_1"),
         InlineKeyboardButton(f"Ячейка 2", callback_data="cell_2")],
        [InlineKeyboardButton(f"Ячейка 3", callback_data="cell_3"),
         InlineKeyboardButton(f"Ячейка 4", callback_data="cell_4")],
        [InlineKeyboardButton("Создать событие", callback_data="create_event"),
        InlineKeyboardButton("Мои события", callback_data="view_events"),
        InlineKeyboardButton("Редактировать событие", callback_data="edit_event"),
        InlineKeyboardButton("Удалить событие", callback_data="delete_event")],
        [InlineKeyboardButton("Меню", callback_data="menu")],
        [InlineKeyboardButton("Просмотр команд", callback_data="show_commands")],
        # [InlineKeyboardButton("Очистить историю бота", callback_data="clear")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    if update.message:
        await update.message.reply_text("Выберите действие:", reply_markup=reply_markup)
    elif update.callback_query:
        query = update.callback_query
        await query.answer()
        await query.edit_message_text("Выберите действие:", reply_markup=reply_markup)


async def handle_grid_action(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Handle actions on the grid (e.g., view profile, manage events)."""
    query = update.callback_query
    await query.answer()

    try:
        if query.data == "view_profile":
            async with get_async_session() as session:
                user_id = convert_telegram_id_to_uuid(update.effective_user.id)
                user = await session.get(User, user_id)

                if user:
                    profile = (
                        f"👤 Ваш профиль:\n"
                        f"Имя: {user.first_name}\n"
                        f"Фамилия: {user.last_name}\n"
                        f"Возраст: {user.age}\n"
                        f"Опыт: {user.experience}\n"
                    )
                    await query.message.edit_text(profile)
                else:
                    await query.message.edit_text("Профиль не найден.")

        elif query.data == "menu":
            await show_menu(update, context)

        elif query.data == "show_commands":
            await show_commands(update, context)

        elif query.data == "create_event":
            return await start_event_creation(update, context)

        elif query.data == "view_events":
            return await view_events(update, context)

        elif query.data == "edit_event":
            await list_events_edit(update, context)

        elif query.data == "delete_event":
            await list_events_delete(update, context)

        else:
            await query.message.edit_text(f"Неизвестный выбор: {query.data}")

    except Exception as e:
        print(f"Ошибка в handle_grid_action: {e}")
        await query.message.edit_text("Произошла ошибка при обработке вашего выбора.")


async def cancel_action(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Обработка отмены действия (например, отмена удаления/редактирования события)."""
    query = update.callback_query
    await query.answer()

    await query.edit_message_text("Действие отменено. Вы можете вернуться в меню или выполнить другое действие.")

    await show_menu(update, context)
