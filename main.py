import os
import asyncio
import threading
import requests
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    ContextTypes,
    CallbackQueryHandler
)
from apscheduler.schedulers.background import BackgroundScheduler

from users_db import init_db, add_user, get_users

TOKEN = os.getenv("BOT_TOKEN")

# PUNE CHAT ID-UL TAU AICI
ADMIN_ID = 123456789

app = Flask(__name__)

init_db()

bot_app = Application.builder().token(TOKEN).build()

# =========================
# CALENDAR
# =========================

def get_calendar():
    try:
        url = "https://nfs.faireconomy.media/ff_calendar_thisweek.json"
        data = requests.get(url, timeout=10).json()

        high_events = []

        for event in data:
            impact = str(event.get("impact", "")).lower()

            if "high" in impact:
                title = event.get("title", "Unknown")
                country = event.get("country", "")

                high_events.append(
                    f"🔴 {country} - {title}"
                )

        if not high_events:
            return "📅 Nu sunt evenimente HIGH impact."

        return (
            "📅 HIGH IMPACT CALENDAR\n\n"
            + "\n".join(high_events[:10])
        )

    except:
        return "Calendar indisponibil."

# =========================
# START
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    add_user(chat_id)

    keyboard = [
        [InlineKeyboardButton("📅 Calendar", callback_data="calendar")],
        [InlineKeyboardButton("📢 News", callback_data="news")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "📊 Economic Bot\n\nAlege:",
        reply_markup=reply_markup
    )

# =========================
# BUTTONS
# =========================

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "calendar":
        await query.message.reply_text(
            get_calendar()
        )

    elif query.data == "news":
        await query.message.reply_text(
            "🔴 Live news engine coming soon"
        )

# =========================
# BROADCAST
# =========================

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_chat.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text(
            "/broadcast mesaj"
        )
        return

    msg = " ".join(context.args)

    users = get_users()
    sent = 0

    for u in users:
        try:
            await bot_app.bot.send_message(
                chat_id=u,
                text=msg
            )
            sent += 1
        except:
            pass

    await update.message.reply_text(
        f"Trimis la {sent} useri"
    )

# =========================
# CALENDAR CMD
# =========================

async def calendar_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(
        get_calendar()
    )

# =========================
# DAILY 07:00
# =========================

def send_daily():
    msg = get_calendar()
    users = get_users()

    async def send():
        for u in users:
            try:
                await bot_app.bot.send_message(
                    chat_id=u,
                    text=msg
                )
            except:
                pass

    asyncio.run(send())

scheduler = BackgroundScheduler()
scheduler.add_job(
    send_daily,
    "cron",
    hour=7,
    minute=0
)
scheduler.start()

# =========================
# HANDLERS
# =========================

bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CommandHandler("calendar", calendar_cmd))
bot_app.add_handler(CommandHandler("broadcast", broadcast))
bot_app.add_handler(CallbackQueryHandler(button))

# =========================
# RUN
# =========================

async def run():
    await bot_app.initialize()
    await bot_app.start()
    await bot_app.updater.start_polling()
    await asyncio.Event().wait()

@app.route("/")
def home():
    return "BOT RUNNING"

if __name__ == "__main__":
    threading.Thread(
        target=lambda: asyncio.run(run())
    ).start()

    port = int(os.environ.get("PORT", 10000))
    app.run(
        host="0.0.0.0",
        port=port
    )
