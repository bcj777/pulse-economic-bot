import os
import asyncio
import threading
from flask import Flask
from telegram.ext import Application
from apscheduler.schedulers.background import BackgroundScheduler

from users_db import init_db, get_users

TOKEN = os.getenv("BOT_TOKEN")

app = Flask(__name__)

# init database
init_db()

# telegram app
bot_app = Application.builder().token(TOKEN).build()

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
                    text="🕖 TEST DAILY MESSAGE"
                )
            except Exception as e:
                print(e)

    asyncio.run(send())

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
