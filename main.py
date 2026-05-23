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

# init DB
init_db()

# telegram app
bot_app = Application.builder().token(TOKEN).build()

# ===== START COMMAND =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    add_user(chat_id)

    await update.message.reply_text(
        "📊 Trading News Bot activ\nPrimești alerte high impact 🔴"
    )

bot_app.add_handler(CommandHandler("start", start))

# ===== NEWS ENGINE (REAL STRUCTURE) =====
def get_economic_calendar():
    # placeholder real API hook (ForexFactory / TradingEconomics etc.)
    return "🔴 CPI HIGH IMPACT TODAY\n📉 Volatility expected"

def get_crypto_news():
    return "₿ BTC NEWS: Market moving event detected"

def get_stock_news():
    return "📈 NVDA / TSLA news: volatility spike"

def build_news():
    return f"""
📊 DAILY MARKET BRIEF

{get_economic_calendar()}

{get_crypto_news()}

{get_stock_news()}
"""

# ===== BROADCAST =====
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

# ===== SCHEDULER =====
scheduler = BackgroundScheduler()
scheduler.add_job(send_news, "cron", hour=7, minute=0)
scheduler.start()

# ===== FLASK =====
@app.route("/")
def home():
    return "Bot Running"

# ===== RUN BOT =====
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
