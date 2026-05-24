import os
import json
import time
import threading
import requests
from datetime import datetime

import pytz
from flask import Flask
from apscheduler.schedulers.background import BackgroundScheduler

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# =====================
# CONFIG
# =====================
TOKEN = os.getenv("BOT_TOKEN")
FINNHUB_KEY = os.getenv("FINNHUB_KEY")

ADMIN_ID = 2054196564
DB_FILE = "users.json"

TZ = pytz.timezone("Europe/Chisinau")

# =====================
# FLASK
# =====================
app = Flask(__name__)

@app.route("/")
def home():
    return "BOT RUNNING"

# =====================
# USERS DB
# =====================
def load_users():
    if not os.path.exists(DB_FILE):
        return []
    try:
        return json.load(open(DB_FILE))
    except:
        return []

def save_users(users):
    json.dump(users, open(DB_FILE, "w"))

def add_user(uid):
    users = load_users()
    if uid not in users:
        users.append(uid)
        save_users(users)

def get_users():
    return load_users()

# =====================
# MEMORY
# =====================
seen_news = set()

# =====================
# CLASSIFY
# =====================
def classify(text):
    t = text.lower()

    if any(x in t for x in ["btc","crypto","bitcoin","eth","ethereum"]):
        return "🟣 CRYPTO"

    if any(x in t for x in ["forex","usd","eur","fed","cpi","inflation","rate"]):
        return "🟢 FOREX"

    if any(x in t for x in ["stock","nasdaq","dow","apple","tesla","nvidia","earnings"]):
        return "🔵 STOCK"

    return "🟠 MACRO"

# =====================
# SENTIMENT
# =====================
def sentiment(text):
    t = text.lower()

    bull = ["rise","rally","surge","growth","strong","gain","up"]
    bear = ["fall","drop","crash","weak","loss","down"]

    score = 0

    for w in bull:
        if w in t:
            score += 1

    for w in bear:
        if w in t:
            score -= 1

    if score >= 2:
        return "🟢 BULLISH"
    elif score <= -2:
        return "🔴 BEARISH"
    else:
        return "⚪ NEUTRAL"

# =====================
# NEWS
# =====================
def fetch_news():
    try:
        url = f"https://finnhub.io/api/v1/news?category=general&token={FINNHUB_KEY}"
        data = requests.get(url, timeout=10).json()

        now = time.time()
        last_48h = 48 * 3600

        news_list = []
        alerts = []

        for n in data:

            title = n.get("headline","")
            summary = n.get("summary","")
            image = n.get("image","")
            link = n.get("url","")
            ts = n.get("datetime", 0)

            if not title:
                continue

            if ts and (now - ts > last_48h):
                continue

            cat = classify(title + summary)
            sent = sentiment(title + summary)

            msg = {
                "text":
                    f"{cat}\n"
                    f"{sent}\n\n"
                    f"<b>{title}</b>\n\n"
                    f"{summary[:250]}\n\n"
                    f"🔗 {link}",
                "image": image
            }

            news_list.append(msg)

            if title not in seen_news:
                seen_news.add(title)
                alerts.append(msg)

        return news_list, alerts

    except:
        return [], []

# =====================
# CALENDAR
# =====================
def fetch_calendar():

    try:
        today = datetime.utcnow().strftime("%Y-%m-%d")

        url = f"https://finnhub.io/api/v1/calendar/economic?token={FINNHUB_KEY}"
        data = requests.get(url, timeout=10).json()

        events = data.get("economicCalendar", [])

        out = []

        for e in events:

            if str(e.get("date")) != today:
                continue

            if "high" not in str(e.get("impact","")).lower():
                continue

            out.append(
                f"📅 ECONOMIC EVENT\n\n"
                f"🌍 {e.get('country')}\n"
                f"⏰ {e.get('time')}\n"
                f"📊 {e.get('event')}"
            )

        return "\n\n---\n\n".join(out) if out else "No events today."

    except:
        return "Calendar error"

# =====================
# START
# =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.effective_user.id
    add_user(uid)

    kb = [
        [InlineKeyboardButton("📰 News", callback_data="news")],
        [InlineKeyboardButton("📅 Calendar", callback_data="calendar")],
        [InlineKeyboardButton("⚙️ Admin Panel", callback_data="panel")]
    ]

    await update.message.reply_text(
        "🚀 BOT ACTIVE",
        reply_markup=InlineKeyboardMarkup(kb)
    )

# =====================
# PANEL (ADMIN DASHBOARD)
# =====================
async def panel(update: Update, context: ContextTypes.DEFAULT_TYPE):

    uid = update.effective_user.id

    if uid != ADMIN_ID:
        await update.message.reply_text("⛔ Not admin")
        return

    kb = [
        [InlineKeyboardButton("👥 List Users", callback_data="list")],
        [InlineKeyboardButton("📢 Broadcast", callback_data="broadcast")]
    ]

    await update.message.reply_text(
        f"⚙️ ADMIN PANEL\nUsers: {len(get_users())}",
        reply_markup=InlineKeyboardMarkup(kb)
    )

# =====================
# CALLBACKS
# =====================
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    uid = q.from_user.id

    if q.data == "news":

        news, _ = fetch_news()

        for n in news:
            if n["image"]:
                await q.message.reply_photo(n["image"], caption=n["text"], parse_mode="HTML")
            else:
                await q.message.reply_text(n["text"], parse_mode="HTML")

    elif q.data == "calendar":

        await q.message.reply_text(fetch_calendar())

    elif q.data == "panel":

        await panel(update, context)

    elif q.data == "list":

        if uid != ADMIN_ID:
            return

        users = get_users()
        await q.message.reply_text("👥 USERS:\n" + "\n".join(map(str, users[:50])))

    elif q.data == "broadcast":

        if uid != ADMIN_ID:
            return

        await q.message.reply_text("Use: /broadcast message")

# =====================
# COMMANDS
# =====================
async def news_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):

    news, _ = fetch_news()

    for n in news:
        if n["image"]:
            await update.message.reply_photo(n["image"], caption=n["text"], parse_mode="HTML")
        else:
            await update.message.reply_text(n["text"], parse_mode="HTML")

async def calendar_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):

    await update.message.reply_text(fetch_calendar())

async def broadcast_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    msg = " ".join(context.args)

    if not msg:
        await update.message.reply_text("Usage: /broadcast message")
        return

    for u in get_users():
        try:
            bot_app.bot.send_message(u, f"📢 {msg}")
        except:
            pass

    await update.message.reply_text("Sent.")

# =====================
# AUTO NEWS LOOP
# =====================
def auto_loop():

    while True:
        try:

            _, alerts = fetch_news()

            for a in alerts:
                for u in get_users():
                    try:
                        if a["image"]:
                            bot_app.bot.send_photo(u, a["image"], a["text"], parse_mode="HTML")
                        else:
                            bot_app.bot.send_message(u, a["text"], parse_mode="HTML")
                    except:
                        pass

            time.sleep(60)

        except:
            time.sleep(60)

# =====================
# SCHEDULER 7AM
# =====================
def send_morning():

    msg = fetch_calendar()

    for u in get_users():
        try:
            bot_app.bot.send_message(u, "🌅 DAILY CALENDAR\n\n" + msg)
        except:
            pass

def start_scheduler():

    scheduler = BackgroundScheduler(timezone=TZ)

    scheduler.add_job(
        send_morning,
        "cron",
        day_of_week="mon-fri",
        hour=7,
        minute=0
    )

    scheduler.start()

# =====================
# BOT INIT
# =====================
bot_app = Application.builder().token(TOKEN).build()

bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CommandHandler("news", news_cmd))
bot_app.add_handler(CommandHandler("calendar", calendar_cmd))
bot_app.add_handler(CommandHandler("panel", panel))
bot_app.add_handler(CommandHandler("broadcast", broadcast_cmd))
bot_app.add_handler(CallbackQueryHandler(buttons))

# =====================
# WEB
# =====================
app_flask = app

def run_web():
    port = int(os.environ.get("PORT", 10000))
    app_flask.run(host="0.0.0.0", port=port)

# =====================
# START
# =====================
if __name__ == "__main__":

    threading.Thread(target=run_web, daemon=True).start()
    threading.Thread(target=auto_loop, daemon=True).start()

    start_scheduler()

    bot_app.run_polling(drop_pending_updates=True)
