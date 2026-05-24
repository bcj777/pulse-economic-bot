import os
import threading
import time
import requests
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# =====================
# CONFIG
# =====================
TOKEN = os.getenv("BOT_TOKEN")
FINNHUB_KEY = os.getenv("FINNHUB_KEY")

ADMIN_ID = 2054196564

# =====================
# APP INIT
# =====================
app = Application.builder().token(TOKEN).build()
web = Flask(__name__)

users = set()
seen_news = set()

# =====================
# WEB
# =====================
@web.route("/")
def home():
    return "BOT RUNNING"

# =====================
# DB SIMPLE
# =====================
def add_user(user_id):
    users.add(user_id)

def get_users():
    return list(users)

# =====================
# NEWS
# =====================
def fetch_news():
    try:
        url = f"https://finnhub.io/api/v1/news?category=general&token={FINNHUB_KEY}"
        data = requests.get(url).json()

        news = []

        for n in data[:10]:
            title = n.get("headline", "")
            image = n.get("image", "")

            msg = {
                "text": f"<b>{title}</b>",
                "image": image
            }

            news.append(msg)

        return news

    except:
        return []

# =====================
# START
# =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    user_id = update.effective_user.id
    add_user(user_id)

    keyboard = [
        [InlineKeyboardButton("📰 News", callback_data="news")]
    ]

    if user_id == ADMIN_ID:
        keyboard.append(
            [InlineKeyboardButton("⚙️ Admin", callback_data="admin")]
        )

    await update.message.reply_text(
        "BOT ACTIVE",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# =====================
# CALLBACKS
# =====================
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    if q.data == "news":

        news = fetch_news()

        for n in news:

            if n["image"]:
                await q.message.reply_photo(n["image"], caption=n["text"], parse_mode="HTML")
            else:
                await q.message.reply_text(n["text"], parse_mode="HTML")

    elif q.data == "admin" and q.from_user.id == ADMIN_ID:

        await q.message.reply_text(f"Users: {len(users)}")

# =====================
# LOOP (optional)
# =====================
def run_web():
    port = int(os.environ.get("PORT", 10000))
    web.run(host="0.0.0.0", port=port)

# =====================
# MAIN
# =====================
if __name__ == "__main__":

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))

    threading.Thread(target=run_web, daemon=True).start()

    print("BOT RUNNING")

    app.run_polling()
