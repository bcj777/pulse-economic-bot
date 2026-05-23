import os
import asyncio
import threading
import time
import requests
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler

from users_db import init_db, add_user, get_users

TOKEN = os.getenv("BOT_TOKEN")
FINNHUB_KEY = os.getenv("FINNHUB_KEY")
ADMIN_ID = 2054196564

app = Flask(__name__)
init_db()

bot_app = Application.builder().token(TOKEN).build()

# =========================
# START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    add_user(chat_id)

    keyboard = [
        [InlineKeyboardButton("📅 Calendar", callback_data="calendar")],
        [InlineKeyboardButton("📰 News", callback_data="news")]
    ]

    await update.message.reply_text(
        "*📊 Trading Intelligence Bot LIVE*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# =========================
# ECONOMIC CALENDAR (REAL)
# =========================
def get_calendar():
    try:
        url = f"https://finnhub.io/api/v1/calendar/economic?token={FINNHUB_KEY}"
        data = requests.get(url, timeout=10).json()

        events = data.get("economicCalendar", [])

        out = []
        for e in events[:10]:
            out.append(
                f"📊 {e.get('event')} | {e.get('country')} | impact: {e.get('impact')}"
            )

        return "*📅 ECONOMIC CALENDAR*\n\n" + "\n".join(out)

    except:
        return "Calendar error"

# =========================
# NEWS ENGINE (REAL API)
# =========================
seen = set()

def get_news():
    alerts = []

    try:
        url = f"https://finnhub.io/api/v1/news?category=general&token={FINNHUB_KEY}"
        data = requests.get(url, timeout=10).json()

        for item in data[:10]:
            headline = item.get("headline", "")

            key = headline
            if key in seen:
                continue
            seen.add(key)

            keywords = [
                "fed", "inflation", "rate", "cpi", "nfp",
                "stock", "crash", "earnings", "crypto", "bitcoin"
            ]

            if any(k in headline.lower() for k in keywords):
                alerts.append(f"🚨 NEWS IMPACT\n\n{headline}")

    except:
        pass

    return alerts

# =========================
# NEWS LOOP (24/7)
# =========================
def news_loop():
    while True:
        news = get_news()

        if news:
            users = get_users()

            async def send():
                for u in users:
                    for n in news:
                        try:
                            await bot_app.bot.send_message(chat_id=u, text=n)
                        except:
                            pass

            asyncio.run(send())

        time.sleep(120)

# =========================
# BUTTONS
# =========================
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.data == "calendar":
        await q.message.reply_text(get_calendar(), parse_mode="Markdown")

    if q.data == "news":
        await q.message.reply_text("📰 News engine active")

# =========================
# INFO
# =========================
async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_ID:
        return

    users = get_users()
    text = f"👥 USERS: {len(users)}\n\n"

    for u in users[:50]:
        text += f"{u}\n"

    await update.message.reply_text(text)

# =========================
# BROADCAST
# =========================
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_ID:
        return

    msg = " ".join(context.args)

    users = get_users()
    sent = 0

    for u in users:
        try:
            await bot_app.bot.send_message(chat_id=u, text=f"📢 {msg}")
            sent += 1
        except:
            pass

    await update.message.reply_text(f"Sent: {sent}")

# =========================
# RUN BOT
# =========================
async def run():
    await bot_app.initialize()
    await bot_app.start()
    await bot_app.updater.start_polling()
    await asyncio.Event().wait()

@app.route("/")
def home():
    return "BOT LIVE"

if __name__ == "__main__":
    threading.Thread(target=lambda: asyncio.run(run())).start()
    threading.Thread(target=news_loop).start()

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
