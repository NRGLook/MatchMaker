from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler,
    Application,
    MessageHandler,
    filters
)

from src.functionality.user.handlers import (
    start,
    button_click,
    handle_input
)
from src.functionality.base.handlers import handle_grid_action, show_menu, show_commands
from src.config.app_config import settings


def main() -> None:
    """The main entry point for launching a Telegram bot."""
    application = Application.builder().token(settings.API_KEY).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('menu', show_menu))
    application.add_handler(CommandHandler('show_commands', show_commands))
    application.add_handler(
        CallbackQueryHandler(
            button_click,
            pattern="^(start_input|skip_input|edit_profile)$")
    )
    application.add_handler(
        CallbackQueryHandler(handle_grid_action, pattern="^(cell_\\d+|view_profile|menu)$")
    )
    application.add_handler(
        MessageHandler(
            filters.TEXT,
            handle_input
        )
    )

    application.run_polling()

if __name__ == "__main__":
    main()
