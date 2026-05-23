import os
import asyncio
import threading
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes
from apscheduler.schedulers.background import BackgroundScheduler

from users_db import init_db, add_user, get_users

TOKEN = os.getenv("BOT_TOKEN")

# PUNE CHAT ID-UL TAU AICI
ADMIN_ID = 123456789

app = Flask(__name__)

init_db()

bot_app = Application.builder().token(TOKEN).build()

# =====================
# START
# =====================

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    add_user(chat_id)

    await update.message.reply_text(
        "✅ Bot activ!\n🕖 Daily brief 07:00\n🔴 Real-time alerts"
    )

# =====================
# BROADCAST
# =====================

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text(
            "Folosește:\n/broadcast mesaj"
        )
        return

    msg = " ".join(context.args)
    users = get_users()

    sent = 0

    for u in users:
        try:
            await bot_app.bot.send_message(
                chat_id=u,
                text=msg
            )
            sent += 1
        except:
            pass

    await update.message.reply_text(
        f"✅ Trimis la {sent} utilizatori"
    )

# =====================
# DAILY TEST
# =====================

def send_daily():
    users = get_users()

    async def send():
        for u in users:
            try:
                await bot_app.bot.send_message(
                    chat_id=u,
                    text="🕖 Daily test"
                )
            except:
                pass

    asyncio.run(send())

# =====================
# HANDLERS
# =====================

bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CommandHandler("broadcast", broadcast))

# =====================
# SCHEDULER
# =====================

scheduler = BackgroundScheduler()
scheduler.add_job(send_daily, "cron", hour=7, minute=0)
scheduler.start()

# =====================
# BOT LOOP
# =====================

async def run():
    await bot_app.initialize()
    await bot_app.start()
    await bot_app.updater.start_polling()
    await asyncio.Event().wait()

# =====================
# FLASK
# =====================

@app.route("/")
def home():
    return "BOT RUNNING"

# =====================
# START
# =====================

if __name__ == "__main__":
    threading.Thread(target=lambda: asyncio.run(run())).start()

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
