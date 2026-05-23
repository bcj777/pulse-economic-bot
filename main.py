import os
import asyncio
import threading
import requests
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler
from apscheduler.schedulers.background import BackgroundScheduler

from users_db import init_db, add_user, get_users

TOKEN = os.getenv("BOT_TOKEN")

ADMIN_ID = 2054196564

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

        events = []

        for e in data:
            if str(e.get("impact", "")).lower() == "high":
                events.append(f"🔴 {e.get('country')} - {e.get('title')}")

        if not events:
            return "📅 Nu sunt evenimente HIGH impact."

        return "📅 HIGH IMPACT CALENDAR\n\n" + "\n".join(events[:10])

    except:
        return "Calendar indisponibil"

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

    await update.message.reply_text(
        "📊 Trading Bot activ",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# =========================
# BUTTONS
# =========================
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.data == "calendar":
        await q.message.reply_text(get_calendar())

    elif q.data == "news":
        await q.message.reply_text("🔴 News engine coming soon")

# =========================
# /CALENDAR
# =========================
async def calendar_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_calendar())

# =========================
# /BROADCAST (ADMIN ONLY)
# =========================
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text("/broadcast mesaj")
        return

    msg = " ".join(context.args)

    users = get_users()
    sent = 0

    for u in users:
        try:
            await bot_app.bot.send_message(chat_id=u, text=msg)
            sent += 1
        except:
            pass

    await update.message.reply_text(f"Trimis la {sent} useri")

# =========================
# /INFO (ADMIN ONLY)
# =========================
async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_ID:
        return

    users = get_users()

    text = f"👥 TOTAL USERS: {len(users)}\n\n"

    for u in users:
        try:
            chat = await bot_app.bot.get_chat(u)

            name = chat.first_name or ""
            username = chat.username or "no_username"

            text += f"• {name} (@{username}) | {u}\n"

        except:
            text += f"• {u}\n"

    await update.message.reply_text(text[:4000])

# =========================
# 07:00 DAILY CALENDAR
# =========================
def send_daily():
    msg = get_calendar()
    users = get_users()

    async def run():
        for u in users:
            try:
                await bot_app.bot.send_message(chat_id=u, text=msg)
            except:
                pass

    asyncio.run(run())

scheduler = BackgroundScheduler()
scheduler.add_job(send_daily, "cron", hour=7, minute=0)
scheduler.start()

# =========================
# HANDLERS
# =========================
bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CommandHandler("calendar", calendar_cmd))
bot_app.add_handler(CommandHandler("broadcast", broadcast))
bot_app.add_handler(CommandHandler("info", info))
bot_app.add_handler(CallbackQueryHandler(button))

# =========================
# BOT RUN
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

if __name__ == "__main__":
    threading.Thread(target=lambda: asyncio.run(run())).start()

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
