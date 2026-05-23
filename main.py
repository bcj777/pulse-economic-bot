import os
import asyncio
import threading
from flask import Flask
from telegram.ext import Application
from apscheduler.schedulers.background import BackgroundScheduler

from db import init, get_all
from engine import build_brief
from bot import register

TOKEN = os.getenv("BOT_TOKEN")

app = Flask(__name__)

init()

bot_app = Application.builder().token(TOKEN).build()
register(bot_app)

# =====================
# DAILY SEND
# =====================

def send_daily():
    msg = build_brief()
    users = get_all()

    async def send():
        for u in users:
            try:
                await bot_app.bot.send_message(u, msg)
            except:
                pass

    asyncio.run(send())

# =====================
# SCHEDULER 07:00
# =====================

scheduler = BackgroundScheduler()
scheduler.add_job(send_daily, "cron", hour=7, minute=0)
scheduler.start()

# =====================
# REAL BOT LOOP
# =====================

async def run():
    await bot_app.initialize()
    await bot_app.start()
    await asyncio.Event().wait()

# =====================
# FLASK ROUTE
# =====================

@app.route("/")
def home():
    return "PRO v1 RUNNING"

# =====================
# START
# =====================

if __name__ == "__main__":
    threading.Thread(target=lambda: asyncio.run(run())).start()

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
