import os
import asyncio
import requests
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from apscheduler.schedulers.background import BackgroundScheduler

from users_db import init_db, add_user, get_users

TOKEN = os.getenv("BOT_TOKEN")

app = Flask(__name__)
init_db()

bot_app = Application.builder().token(TOKEN).build()

# =========================
# 🧠 SCORE ENGINE
# =========================

def score_event(text):
    keywords_red = ["CPI", "NFP", "RATE", "FOMC", "INFLATION"]
    keywords_high = ["BTC", "ETH", "NASDAQ", "S&P", "NASDAQ"]

    t = text.upper()

    if any(k in t for k in keywords_red):
        return "🔴 RED IMPACT"
    if any(k in t for k in keywords_high):
        return "🟠 HIGH IMPACT"
    return "🟡 MEDIUM"

# =========================
# 📊 ECONOMIC CALENDAR (SIMPLIFIED API HOOK)
# =========================

def get_economic_calendar():
    # placeholder for TradingEconomics / ForexFactory scraping later
    events = [
        "CPI Inflation Report",
        "Unemployment Rate NFP",
        "FOMC Meeting Minutes"
    ]

    output = []
    for e in events:
        score = score_event(e)
        if "RED" in score:
            output.append(f"{score} → {e}")

    return "\n".join(output)

# =========================
# ₿ CRYPTO DATA (CoinGecko SIMPLE)
# =========================

def get_crypto():
    try:
        url = "https://api.coingecko.com/api/v3/simple/price"
        params = {
            "ids": "bitcoin,ethereum",
            "vs_currencies": "usd",
            "include_24hr_change": "true"
        }

        r = requests.get(url, params=params).json()

        btc = r["bitcoin"]["usd"]
        btc_chg = r["bitcoin"]["usd_24h_change"]

        eth = r["ethereum"]["usd"]
        eth_chg = r["ethereum"]["usd_24h_change"]

        return f"""
₿ CRYPTO MARKET
BTC: ${btc} ({btc_chg:.2f}%)
ETH: ${eth} ({eth_chg:.2f}%)
"""
    except:
        return "₿ CRYPTO ERROR"

# =========================
# 📈 STOCKS (SIMPLIFIED MOCK LOGIC)
# =========================

def get_stocks():
    # placeholder (later AlphaVantage / Yahoo Finance)
    return """
📈 STOCKS
NVDA: +2.3%
TSLA: -1.1%
AAPL: +0.8%
"""

# =========================
# 🧠 FINAL NEWS BUILDER
# =========================

def build_news():
    return f"""
📊 MARKET INTELLIGENCE TERMINAL

{get_economic_calendar()}

{get_crypto()}

{get_stocks()}
"""

# =========================
# 📤 BROADCAST
# =========================

def send_news():
    message = build_news()
    users = get_users()

    async def send_all():
        for chat_id in users:
            try:
                await bot_app.bot.send_message(chat_id=chat_id, text=message)
            except:
                pass

    asyncio.run(send_all())

# =========================
# 🤖 COMMANDS
# =========================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    add_user(chat_id)

    await update.message.reply_text(
        "📊 Market Intelligence Bot ACTIVE\n🔴 High-impact alerts enabled"
    )

bot_app.add_handler(CommandHandler("start", start))

# =========================
# ⏰ SCHEDULER
# =========================

scheduler = BackgroundScheduler()
scheduler.add_job(send_news, "cron", hour=7, minute=0)
scheduler.start()

# =========================
# 🌐 FLASK SERVER
# =========================

@app.route("/")
def home():
    return "Market Intelligence Bot Running"

# =========================
# 🚀 RUN
# =========================

async def run_bot():
    await bot_app.initialize()
    await bot_app.start()
    await bot_app.updater.start_polling()
    await asyncio.Event().wait()

if __name__ == "__main__":
    import threading

    threading.Thread(target=lambda: asyncio.run(run_bot())).start()

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
