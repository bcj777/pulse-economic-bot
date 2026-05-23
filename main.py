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
# 🧠 PRIORITY ENGINE (LEVEL 5)
# =========================

def priority(label):
    return {
        "CRITICAL": "🔴 CRITICAL",
        "IMPORTANT": "🟠 IMPORTANT",
        "INFO": "🟡 INFO"
    }.get(label, "🟡 INFO")

# =========================
# 🌍 MACRO CALENDAR (FILTERED)
# =========================

def get_macro():
    # placeholder for TradingEconomics API later
    events = [
        ("CPI Inflation YoY", "CRITICAL"),
        ("NFP Employment Data", "CRITICAL"),
        ("Retail Sales", "IMPORTANT")
    ]

    out = []
    for name, lvl in events:
        if lvl == "CRITICAL":
            out.append(f"{priority(lvl)} → {name}")

    return "\n".join(out)

# =========================
# ₿ CRYPTO INTELLIGENCE
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

        def trend(x):
            if x > 2:
                return "📈 STRONG UP"
            elif x < -2:
                return "📉 STRONG DOWN"
            return "➡️ SIDEWAYS"

        return f"""
₿ CRYPTO INTELLIGENCE
BTC: ${btc} ({btc_chg:.2f}%) {trend(btc_chg)}
ETH: ${eth} ({eth_chg:.2f}%) {trend(eth_chg)}
"""
    except:
        return "₿ CRYPTO ERROR"

# =========================
# 📊 STOCK INTELLIGENCE (SIMPLIFIED)
# =========================

def get_stocks():
    # placeholder logic (upgrade later with real API)
    return """
📈 STOCK MARKET
NVDA → 📈 STRONG UP
TSLA → 📉 WEAK DOWN
AAPL → ➡️ STABLE
"""

# =========================
# 📊 FINAL BRIEF
# =========================

def build_brief():
    return f"""
📊 MARKET INTELLIGENCE BRIEF

🌍 MACRO RISK
{get_macro()}

{get_crypto()}

{get_stocks()}
"""

# =========================
# 📤 BROADCAST SYSTEM
# =========================

def send_brief():
    msg = build_brief()
    users = get_users()

    async def send_all():
        for chat_id in users:
            try:
                await bot_app.bot.send_message(chat_id=chat_id, text=msg)
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
        "📊 Market Intelligence LEVEL 5 ACTIVE\n🔴 Macro risk filtering enabled"
    )

bot_app.add_handler(CommandHandler("start", start))

# =========================
# ⏰ SCHEDULER
# =========================

scheduler = BackgroundScheduler()
scheduler.add_job(send_brief, "cron", hour=7, minute=0)
scheduler.start()

# =========================
# 🌐 FLASK
# =========================

@app.route("/")
def home():
    return "Market Intelligence LEVEL 5 Running"

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
