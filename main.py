from telegram import Update
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ConversationHandler
from src.functionality.user.possibilities import start, handle_input, button_click, show_grid, handle_grid_action

from src.config.app_config import settings

FIRST_NAME, LAST_NAME, AGE, EXPERIENCE, SHOW_GRID = range(5)


def main() -> None:
    TOKEN = settings.API_KEY
    app = Application.builder().token(TOKEN).build()

    conv_handler = ConversationHandler(
        entry_points=[CommandHandler("start", start)],
        states={
            FIRST_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_input)],
            LAST_NAME: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_input)],
            AGE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_input)],
            EXPERIENCE: [MessageHandler(filters.TEXT & ~filters.COMMAND, handle_input)],
            SHOW_GRID: [CallbackQueryHandler(handle_grid_action)],
        },
        fallbacks=[CallbackQueryHandler(button_click)],
    )

    app.add_handler(conv_handler)

    app.run_polling()


if __name__ == "__main__":
    main()
