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
        "📊 Trading Bot ACTIV",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

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

        return "📅 HIGH IMPACT CALENDAR\n\n" + "\n".join(out[:10])

    except:
        return "Calendar error"

# =========================
# BUTTONS
# =========================
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.data == "calendar":
        await q.message.reply_text(get_calendar())

    elif q.data == "news":
        await q.message.reply_text("📰 News engine running...")

# =========================
# NEWS ENGINE (REAL LOGIC)
# =========================
seen = set()

def get_news():
    alerts = []

    try:
        # CRYPTO
        crypto = requests.get(
            "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana&vs_currencies=usd&include_24hr_change=true"
        ).json()

        for coin, data in crypto.items():
            change = data.get("usd_24h_change", 0)

            if abs(change) >= 3:
                key = f"crypto_{coin}"

                if key not in seen:
                    seen.add(key)

                    alerts.append(
                        f"🚨 CRYPTO HIGH IMPACT\n\n{coin.upper()} {change:.2f}%"
                    )

        # STOCKS
        stocks = requests.get(
            "https://query1.finance.yahoo.com/v7/finance/quote?symbols=AAPL,TSLA,NVDA"
        ).json()

        for s in stocks.get("quoteResponse", {}).get("result", []):
            change = s.get("regularMarketChangePercent", 0)

            if abs(change) >= 2:
                symbol = s.get("symbol")
                key = f"stock_{symbol}"

                if key not in seen:
                    seen.add(key)

                    alerts.append(
                        f"🚨 STOCK HIGH IMPACT\n\n{symbol} {change:.2f}%"
                    )

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

            async def run():
                for u in users:
                    for n in news:
                        try:
                            await bot_app.bot.send_message(chat_id=u, text=n)
                        except:
                            pass

            asyncio.run(run())

        time.sleep(120)

# =========================
# HANDLERS
# =========================
bot_app.add_handler(CommandHandler("start", start))
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
    threading.Thread(target=news_loop).start()

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
