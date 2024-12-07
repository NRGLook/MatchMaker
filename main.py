from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton
from telegram.ext import (
    Application,
    CommandHandler,
    MessageHandler,
    CallbackQueryHandler,
    filters,
    ContextTypes,
)

from src.config.app_config import settings


async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    keyboard = [
        [InlineKeyboardButton("1", callback_data="cell_1"), InlineKeyboardButton("2", callback_data="cell_2")],
        [InlineKeyboardButton("3", callback_data="cell_3"), InlineKeyboardButton("4", callback_data="cell_4")],
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    await update.message.reply_text("Выберите ячейку:", reply_markup=reply_markup)


async def echo(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    await update.message.reply_text(f"Вы сказали: {update.message.text}")


async def button_click(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
) -> None:
    query = update.callback_query
    await query.answer()
    await query.edit_message_text(text=f"Вы нажали: {query.data}")


def main():
    TOKEN = settings.API_KEY

    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, echo))
    app.add_handler(CallbackQueryHandler(button_click))

    app.run_polling()


if __name__ == "__main__":
    main()
