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
    user_id = update.effective_chat.id
    add_user(user_id)

    keyboard = [
        [InlineKeyboardButton("📅 Calendar", callback_data="calendar")],
        [InlineKeyboardButton("📰 News", callback_data="news")]
    ]

    # ADMIN ONLY BUTTON
    if user_id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("⚙️ Admin Panel", callback_data="panel")])

    await update.message.reply_text(
        "*📊 Trading Bot ACTIVE*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# =========================
# CALENDAR (WITH DATE + TIME)
# =========================
def get_calendar():
    try:
        url = f"https://finnhub.io/api/v1/calendar/economic?token={FINNHUB_KEY}"
        data = requests.get(url, timeout=10).json()

        events = data.get("economicCalendar", [])

        out = []

        for e in events[:10]:
            date = e.get("date", "no-date")
            time_ = e.get("time", "no-time")

            out.append(
                f"📅 {date} {time_}\n"
                f"📊 {e.get('event')}\n"
                f"🌍 {e.get('country')} | Impact: {e.get('impact')}"
            )

        return "*📅 ECONOMIC CALENDAR*\n\n" + "\n\n".join(out)

    except:
        return "Calendar error"

# =========================
# NEWS ENGINE
# =========================
seen = set()

def get_news():
    alerts = []

    try:
        url = f"https://finnhub.io/api/v1/news?category=general&token={FINNHUB_KEY}"
        data = requests.get(url, timeout=10).json()

        for item in data[:10]:
            headline = item.get("headline", "")

            if headline in seen:
                continue

            seen.add(headline)

            keywords = ["fed", "inflation", "rate", "cpi", "nfp", "stock", "crypto"]

            if any(k in headline.lower() for k in keywords):
                alerts.append(f"🚨 NEWS\n\n{headline}")

    except:
        pass

    return alerts

# =========================
# NEWS LOOP
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
# CALLBACKS (SINGLE HANDLER FIX)
# =========================
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    user_id = q.from_user.id

    # CALENDAR
    if q.data == "calendar":
        await q.message.reply_text(get_calendar(), parse_mode="Markdown")

    # NEWS
    elif q.data == "news":
        await q.message.reply_text("📰 News engine active")

    # ADMIN PANEL (ONLY ADMIN)
    elif q.data == "panel" and user_id == ADMIN_ID:
        keyboard = [
            [InlineKeyboardButton("👥 Users", callback_data="admin_users")],
            [InlineKeyboardButton("📋 Commands", callback_data="admin_list")],
            [InlineKeyboardButton("📊 Status", callback_data="admin_status")]
        ]

        await q.message.reply_text(
            "*⚙️ ADMIN PANEL*",
            parse_mode="Markdown",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    # ADMIN FUNCTIONS
    elif q.data == "admin_users" and user_id == ADMIN_ID:
        users = get_users()
        await q.message.reply_text(f"*Users:* {len(users)}", parse_mode="Markdown")

    elif q.data == "admin_list" and user_id == ADMIN_ID:
        await q.message.reply_text(
            "/info\n/broadcast\n/testnews\n/calendar",
            parse_mode="Markdown"
        )

    elif q.data == "admin_status" and user_id == ADMIN_ID:
        await q.message.reply_text("*System ONLINE*", parse_mode="Markdown")

# =========================
# INFO
# =========================
async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_ID:
        return

    users = get_users()
    text = f"*Users:* {len(users)}\n\n"

    for u in users[:30]:
        text += f"{u}\n"

    await update.message.reply_text(text, parse_mode="Markdown")

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
# REGISTER HANDLERS
# =========================
bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CommandHandler("info", info))
bot_app.add_handler(CommandHandler("broadcast", broadcast))
bot_app.add_handler(CallbackQueryHandler(button))

# =========================
# RUN BOT
# =========================
async def run():
    await bot_app.initialize()
    await bot_app.start()
    await bot_app.run_polling()

@app.route("/")
def home():
    return "BOT RUNNING"

if __name__ == "__main__":
    threading.Thread(target=lambda: asyncio.run(run())).start()
    threading.Thread(target=news_loop).start()

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
