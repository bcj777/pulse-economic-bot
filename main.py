import os
import json
import time
import threading
import requests
from datetime import datetime
from flask import Flask

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, ContextTypes

# =====================
# CONFIG
# =====================
TOKEN = os.getenv("BOT_TOKEN")
FINNHUB_KEY = os.getenv("FINNHUB_KEY")
ADMIN_ID = 2054196564

DB_FILE = "users.json"

# =====================
# FLASK SERVER
# =====================
web = Flask(__name__)

@web.route("/")
def home():
    return "TRADING BOT RUNNING"

# =====================
# DATABASE
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

def add_user(user_id):
    users = load_users()
    if user_id not in users:
        users.append(user_id)
        save_users(users)

def get_users():
    return load_users()

# =====================
# NEWS MEMORY
# =====================
seen_news = set()

# =====================
# CLASSIFY MARKET
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
# SCORE ENGINE
# =====================
def score(text):
    t = text.lower()
    keys = ["fed","cpi","inflation","btc","bitcoin","rate","recession","stocks","crypto"]
    return sum(2 for k in keys if k in t)

# =====================
# NEWS API
# =====================
def fetch_news():
    try:
        url = f"https://finnhub.io/api/v1/news?category=general&token={FINNHUB_KEY}"
        data = requests.get(url, timeout=10).json()

        news_list = []
        alerts = []

        for n in data[:20]:

            title = n.get("headline","")
            summary = n.get("summary","")
            image = n.get("image","")

            if not title:
                continue

            cat = classify(title + summary)
            sc = score(title + summary)

            msg = {
                "text": f"{cat}\n\n<b>{title}</b>\n\n{summary[:250]}",
                "image": image,
                "title": title,
                "score": sc
            }

            news_list.append(msg)

            if sc >= 2 and title not in seen_news:
                seen_news.add(title)
                alerts.append(msg)

        return news_list, alerts

    except:
        return [], []

# =====================
# ECONOMIC CALENDAR
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
                f"📅 <b>ECONOMIC EVENT</b>\n\n"
                f"🌍 {e.get('country')}\n"
                f"⏰ {e.get('time')}\n"
                f"📊 {e.get('event')}"
            )

        return "\n\n━━━━━━━━━━\n\n".join(out) if out else "📅 No events today."

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
        [InlineKeyboardButton("📅 Calendar", callback_data="calendar")]
    ]

    if uid == ADMIN_ID:
        kb.append([InlineKeyboardButton("⚙️ Admin", callback_data="admin")])

    await update.message.reply_text(
        "🚀 <b>TRADING ENGINE ACTIVE</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(kb)
    )

# =====================
# CALLBACKS
# =====================
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):

    q = update.callback_query
    await q.answer()

    if q.data == "news":

        news, _ = fetch_news()

        for n in news:

            if n["image"]:
                await q.message.reply_photo(n["image"], caption=n["text"], parse_mode="HTML")
            else:
                await q.message.reply_text(n["text"], parse_mode="HTML")

    elif q.data == "calendar":

        await q.message.reply_text(fetch_calendar(), parse_mode="HTML")

    elif q.data == "admin" and q.from_user.id == ADMIN_ID:

        await q.message.reply_text(
            f"👥 USERS: {len(get_users())}\n"
            f"/info /broadcast /list"
        )

# =====================
# ADMIN COMMANDS
# =====================
async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    await update.message.reply_text(f"Users: {len(get_users())}")

async def list_cmd(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    await update.message.reply_text("/info /broadcast /list")

async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):

    if update.effective_user.id != ADMIN_ID:
        return

    msg = " ".join(context.args)

    for u in get_users():
        try:
            await context.bot.send_message(u, f"📢 {msg}")
        except:
            pass

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
# BOT SETUP
# =====================
bot_app = Application.builder().token(TOKEN).build()

bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CommandHandler("info", info))
bot_app.add_handler(CommandHandler("list", list_cmd))
bot_app.add_handler(CommandHandler("broadcast", broadcast))
bot_app.add_handler(CallbackQueryHandler(buttons))

# =====================
# WEB SERVER THREAD
# =====================
def run_web():
    port = int(os.environ.get("PORT", 10000))
    web.run(host="0.0.0.0", port=port)

# =====================
# START SYSTEM
# =====================
if __name__ == "__main__":

    threading.Thread(target=run_web, daemon=True).start()
    threading.Thread(target=auto_loop, daemon=True).start()

    bot_app.run_polling(drop_pending_updates=True)
