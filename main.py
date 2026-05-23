import os
import threading
import requests
from flask import Flask

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# =====================
# CONFIG
# =====================
TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 2054196564

# =====================
# FLASK WEB SERVER
# =====================
web = Flask(__name__)

@web.route("/")
def home():
    return "Bot is running ✔"

# =====================
# TELEGRAM BOT
# =====================
app = Application.builder().token(TOKEN).build()

# =====================
# START
# =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("📅 Calendar", callback_data="calendar")],
        [InlineKeyboardButton("📰 News", callback_data="news")]
    ]

    if update.effective_user.id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("⚙️ Admin", callback_data="admin")])

    await update.message.reply_text(
        "🚀 WEB SERVER BOT ACTIVE",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# =====================
# CALLBACKS
# =====================
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.data == "calendar":
        await q.message.reply_text("📅 Calendar OK")

    elif q.data == "news":
        await q.message.reply_text("📰 News OK")

    elif q.data == "admin":
        await q.message.reply_text("⚙️ Admin Panel")

# =====================
# REGISTER HANDLERS
# =====================
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(buttons))

# =====================
# RUN BOT IN THREAD
# =====================
def run_bot():
    print("BOT STARTED")
    app.run_polling()

# =====================
# RUN EVERYTHING
# =====================
if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()

    port = int(os.environ.get("PORT", 10000))
    web.run(host="0.0.0.0", port=port)
