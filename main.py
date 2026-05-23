import os
import asyncio
import threading
import requests
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from apscheduler.schedulers.background import BackgroundScheduler

from users_db import init_db, add_user, get_users

TOKEN = os.getenv("BOT_TOKEN")

app = Flask(__name__)

# DATABASE
init_db()

# TELEGRAM APP
bot_app = Application.builder().token(TOKEN).build()

# =========================
# CALENDAR HIGH IMPACT
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
            return "📅 Azi nu sunt evenimente HIGH impact."

        return (
            "📅 HIGH IMPACT CALENDAR\n\n"
            + "\n".join(high_events[:10])
        )

    except Exception as e:
        print(e)
        return "Calendar momentan indisponibil."

# =========================
# START COMMAND
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    add_user(chat_id)

    await update.message.reply_text(
        "✅ Bot activ!\n\n🕖 Calendar HIGH impact la 07:00\n\nFolosește /calendar pentru test."
    )

# =========================
# /CALENDAR COMMAND
# =========================

async def calendar_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    msg = get_calendar()
    await update.message.reply_text(msg)

# =========================
# DAILY 07:00 SEND
# =========================

def send_daily_calendar():
    msg = get_calendar()
    users = get_users()

    async def send():
        for u in users:
            try:
                await bot_app.bot.send_message(
                    chat_id=u,
                    text=msg
                )
            except Exception as e:
                print(e)

    asyncio.run(send())

# =========================
# HANDLERS
# =========================

bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CommandHandler("calendar", calendar_cmd))

# =========================
# SCHEDULER 07:00
# =========================

scheduler = BackgroundScheduler()
scheduler.add_job(
    send_daily_calendar,
    "cron",
    hour=7,
    minute=0
)
scheduler.start()

# =========================
# BOT LOOP
# =========================

async def run():
    await bot_app.initialize()
    await bot_app.start()
    await bot_app.updater.start_polling()
    await asyncio.Event().wait()

# =========================
# FLASK
# =========================

@app.route("/")
def home():
    return "BOT RUNNING"

# =========================
# START APP
# =========================

if __name__ == "__main__":
    threading.Thread(
        target=lambda: asyncio.run(run())
    ).start()

    port = int(os.environ.get("PORT", 10000))
    app.run(
        host="0.0.0.0",
        port=port
    )
