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
    add_user(update.effective_chat.id)

    keyboard = [
        [InlineKeyboardButton("📅 Calendar", callback_data="calendar")],
        [InlineKeyboardButton("📰 News", callback_data="news")],
        [InlineKeyboardButton("⚙️ Admin Panel", callback_data="panel")]
    ]

    await update.message.reply_text(
        "*📊 TRADING INTELLIGENCE BOT PRO*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# =========================
# FINNHUB CALENDAR
# =========================
def get_calendar():
    try:
        url = f"https://finnhub.io/api/v1/calendar/economic?token={FINNHUB_KEY}"
        data = requests.get(url, timeout=10).json()

        events = data.get("economicCalendar", [])

        out = []
        for e in events[:10]:
            out.append(f"📊 {e.get('event')} | {e.get('country')} | {e.get('impact')}")

        return "*📅 ECONOMIC CALENDAR*\n\n" + "\n".join(out)

    except:
        return "Calendar error"

# =========================
# NEWS ENGINE (REAL)
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
                alerts.append(f"🚨 NEWS\n\n_{headline}_")

    except:
        pass

    return alerts

# =========================
# SAFE LOOP
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
                            await bot_app.bot.send_message(chat_id=u, text=n, parse_mode="Markdown")
                        except:
                            pass

            asyncio.run(send())

        time.sleep(120)

# =========================
# BUTTON HANDLER
# =========================
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.data == "calendar":
        await q.message.reply_text(get_calendar(), parse_mode="Markdown")

    elif q.data == "news":
        await q.message.reply_text("*📰 News active*", parse_mode="Markdown")

    elif q.data == "panel":
        await admin_panel(update, context)

# =========================
# ADMIN PANEL PRO
# =========================
async def admin_panel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_ID:
        return

    keyboard = [
        [InlineKeyboardButton("👥 Users", callback_data="admin_users")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="admin_broadcast")],
        [InlineKeyboardButton("📋 Commands", callback_data="admin_list")],
        [InlineKeyboardButton("📊 System Status", callback_data="admin_status")]
    ]

    await update.effective_message.reply_text(
        "*⚙️ ADMIN PANEL PRO*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# =========================
# ADMIN CALLBACKS
# =========================
async def admin_callbacks(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.from_user.id != ADMIN_ID:
        return

    if q.data == "admin_users":
        users = get_users()
        await q.message.reply_text(f"*Users:* {len(users)}", parse_mode="Markdown")

    elif q.data == "admin_list":
        text = """
*Commands:*
/info
/broadcast
/testnews
/list
"""
        await q.message.reply_text(text, parse_mode="Markdown")

    elif q.data == "admin_status":
        await q.message.reply_text("*System: ONLINE*\nNews: ACTIVE", parse_mode="Markdown")

    elif q.data == "admin_broadcast":
        await q.message.reply_text("Use: /broadcast mesaj")

# =========================
# INFO (ADMIN ONLY)
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
# COMMANDS
# =========================
bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CommandHandler("info", info))
bot_app.add_handler(CommandHandler("broadcast", broadcast))
bot_app.add_handler(CallbackQueryHandler(button))
bot_app.add_handler(CallbackQueryHandler(admin_callbacks))

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
    return "BOT PRO ACTIVE"

if __name__ == "__main__":
    threading.Thread(target=lambda: asyncio.run(run())).start()
    threading.Thread(target=news_loop).start()

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
