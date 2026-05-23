import os
import asyncio
import threading
import time
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

        out = []

        for e in data:
            if str(e.get("impact", "")).lower() == "high":
                out.append(f"🔴 {e.get('country')} - {e.get('title')}")

        if not out:
            return "📅 Nu sunt evenimente HIGH impact."

        return "📅 HIGH IMPACT CALENDAR\n\n" + "\n".join(out[:10])

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
        "📊 Economic Bot activ",
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
        await q.message.reply_text("🔴 News engine loading...")

# =========================
# CALENDAR CMD
# =========================
async def calendar_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text(get_calendar())

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
            await bot_app.bot.send_message(u, msg)
            sent += 1
        except:
            pass

    await update.message.reply_text(f"Trimis la {sent} useri")

# =========================
# 07:00 CALENDAR
# =========================
def send_daily():
    msg = get_calendar()
    users = get_users()

    async def run():
        for u in users:
            try:
                await bot_app.bot.send_message(u, msg)
            except:
                pass

    asyncio.run(run())

scheduler = BackgroundScheduler()
scheduler.add_job(send_daily, "cron", hour=7, minute=0)
scheduler.start()

# =========================
# CRYPTO ENGINE (HIGH IMPACT)
# =========================
def get_crypto_alerts():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana&vs_currencies=usd&include_24hr_change=true"
        data = requests.get(url, timeout=10).json()

        alerts = []

        for coin, info in data.items():
            change = info.get("usd_24h_change", 0)

            if abs(change) >= 2:
                direction = "📈" if change > 0 else "📉"
                alerts.append(f"{direction} {coin.upper()} {change:.2f}%")

        if not alerts:
            return None

        return "₿ CRYPTO HIGH IMPACT\n\n" + "\n".join(alerts)

    except:
        return None

def crypto_loop():
    while True:
        msg = get_crypto_alerts()

        if msg:
            users = get_users()

            async def run():
                for u in users:
                    try:
                        await bot_app.bot.send_message(u, msg)
                    except:
                        pass

            asyncio.run(run())

        time.sleep(300)

# =========================
# HANDLERS
# =========================
bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CommandHandler("calendar", calendar_cmd))
bot_app.add_handler(CommandHandler("broadcast", broadcast))
bot_app.add_handler(CallbackQueryHandler(button))

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
    return "BOT RUNNING"

if __name__ == "__main__":
    threading.Thread(target=lambda: asyncio.run(run())).start()
    threading.Thread(target=crypto_loop).start()

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
