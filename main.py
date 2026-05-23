import os
import asyncio
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from apscheduler.schedulers.background import BackgroundScheduler

TOKEN = os.getenv("BOT_TOKEN")

# ===== STORAGE USERS (multi-user) =====
users = set()

# ===== TELEGRAM APP =====
bot_app = Application.builder().token(TOKEN).build()

# ===== FLASK =====
app = Flask(__name__)

# ===== COMMAND: START =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id

    # adăugăm user-ul în listă
    users.add(chat_id)

    await update.message.reply_text(
        "📊 Bot activ!\nVei primi știri zilnice la 07:00."
    )

bot_app.add_handler(CommandHandler("start", start))

# ===== NEWS (placeholder acum) =====
def get_economic_news():
    return "🔴 HIGH IMPACT NEWS\n📉 Market volatility expected"

# ===== BROADCAST FUNCTION =====
def send_daily_news():
    message = get_economic_news()

    async def send_all():
        for chat_id in list(users):
            try:
                await bot_app.bot.send_message(chat_id=chat_id, text=message)
            except:
                pass

    asyncio.run(send_all())

# ===== SCHEDULER (07:00) =====
scheduler = BackgroundScheduler()
scheduler.add_job(send_daily_news, "cron", hour=7, minute=0)
scheduler.start()

# ===== ROUTE (Render needs port) =====
@app.route("/")
def home():
    return "Bot is running"

# ===== START BOT =====
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
