from telegram import Update
from telegram.ext import CommandHandler, ContextTypes
from db import add

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    add(chat_id)

    await update.message.reply_text(
        "📊 PRO v1 ACTIVE\n🕖 Daily brief + 🔴 real-time alerts"
    )


def register(app):
    app.add_handler(CommandHandler("start", start))
