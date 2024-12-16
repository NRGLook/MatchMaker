from telegram.ext import (
    CommandHandler,
    CallbackQueryHandler,
    Application,
    MessageHandler,
    filters,
)

from src.functionality.event.handlers import (
    get_event_conversation_handler,
    handle_event_action,
    list_events_edit,
    list_events_delete,
    handle_event_edit
)
from src.functionality.team.handlers import handle_team_input, start_team_creation, view_teams, list_teams_delete, \
    handle_team_action, get_team_conversation_handler, list_teams_edit, handle_team_edit
from src.functionality.user.handlers import (
    start,
    button_click,
    handle_input
)
from src.functionality.base.handlers import (
    handle_grid_action,
    show_menu,
    show_commands,
    empty_commands,
    cancel_action
)
from src.config.app_config import settings


def main() -> None:
    """The main entry point for launching a Telegram bot."""
    application = Application.builder().token(settings.API_KEY).build()

    application.add_handler(CommandHandler('start', start))
    application.add_handler(CommandHandler('menu', show_menu))
    application.add_handler(CommandHandler('show_commands', show_commands))
    application.add_handler(CommandHandler('empty', empty_commands))

    application.add_handler(get_event_conversation_handler())
    application.add_handler(CallbackQueryHandler(list_events_edit, pattern="^edit_event$"))
    application.add_handler(CallbackQueryHandler(list_events_delete, pattern="^delete_event$"))
    application.add_handler(CallbackQueryHandler(handle_event_action, pattern="^(edit|delete)_([a-f0-9-]+)$"))
    application.add_handler(
        MessageHandler(
            filters.TEXT & filters.UpdateType.MESSAGE,
            handle_event_edit
        )
    )

    application.add_handler(get_team_conversation_handler())
    application.add_handler(CallbackQueryHandler(list_teams_edit, pattern="^edit_team$"))
    application.add_handler(CallbackQueryHandler(list_teams_delete, pattern="^delete_team$"))
    application.add_handler(CallbackQueryHandler(handle_team_action, pattern="^(edit|delete)_([a-f0-9-]+)$"))
    application.add_handler(
        MessageHandler(
            filters.TEXT & filters.UpdateType.MESSAGE,
            handle_team_edit
        )
    )

    application.add_handler(
        CallbackQueryHandler(
            button_click,
            pattern="^(start_input|skip_input|edit_profile)$"
        )
    )
    application.add_handler(
        CallbackQueryHandler(
            handle_grid_action,
            pattern="^(cell_\\d+|view_profile|menu|show_commands|"
                    "create_event|view_events|edit_events|delete_events|"
                    "create_team|view_teams|edit_team|delete_team|)$"
        )
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
