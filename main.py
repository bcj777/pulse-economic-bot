import os
import json
import time
import threading
import requests
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
# FLASK
# =====================
web = Flask(__name__)

@web.route("/")
def home():
    return "PRO BOT RUNNING"

# =====================
# DB
# =====================
def load_users():
    if not os.path.exists(DB_FILE):
        return []
    return json.load(open(DB_FILE))

def save_users(data):
    json.dump(data, open(DB_FILE, "w"))

def add_user(uid):
    users = load_users()
    if uid not in users:
        users.append(uid)
        save_users(users)

def get_users():
    return load_users()

# =====================
# NEWS STATE
# =====================
seen_news = set()

# =====================
# CLASSIFICATION ENGINE
# =====================
def classify(text):
    t = text.lower()

    if any(x in t for x in ["btc","crypto","bitcoin","eth","ethereum"]):
        return "🟣 CRYPTO"

    if any(x in t for x in ["usd","eur","forex","fed","cpi","inflation","rate"]):
        return "🟢 FOREX"

    if any(x in t for x in ["stock","nasdaq","dow","apple","tesla","nvidia","earnings"]):
        return "🔵 STOCK"

    return "🟠 MACRO"

# =====================
# SCORE ENGINE
# =====================
def score(text):
    t = text.lower()
    keywords = ["fed","cpi","inflation","btc","bitcoin","rate","recession","stocks","crypto"]
    return sum(2 for k in keywords if k in t)

# =====================
# NEWS API
# =====================
def fetch_news():
    try:
        url = f"https://finnhub.io/api/v1/news?category=general&token={FINNHUB_KEY}"
        data = requests.get(url).json()

        results = []
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
                "id": title,
                "text": f"{cat}\n\n<b>{title}</b>\n\n{summary[:250]}",
                "image": image,
                "score": sc
            }

            results.append(msg)

            if sc >= 2 and title not in seen_news:
                seen_news.add(title)
                alerts.append(msg)

        return results, alerts

    except:
        return [], []

# =====================
# CALENDAR
# =====================
def fetch_calendar():
    try:
        url = f"https://finnhub.io/api/v1/calendar/economic?token={FINNHUB_KEY}"
        data = requests.get(url).json()

        events = data.get("economicCalendar", [])
        out = []

        for e in events:
            if "high" in str(e.get("impact","")).lower():
                out.append(
                    f"📅 HIGH IMPACT\n\n"
                    f"{e.get('date')} {e.get('time')}\n"
                    f"{e.get('event')}\n"
                    f"{e.get('country')}"
                )

        return "\n\n━━━━━━━━━━\n\n".join(out) if out else "No high impact events."

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
        "🚀 PRO TRADING ENGINE ACTIVE",
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

        users = get_users()

        await q.message.reply_text(
            f"👥 USERS: {len(users)}\n"
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
# AUTO ENGINE
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
# RUN
# =====================
web_app = Application.builder().token(TOKEN).build()
bot_app = web_app

web_server = Flask(__name__)

@web_server.route("/")
def home():
    return "OK"

def run_web():
    port = int(os.environ.get("PORT", 10000))
    web_server.run(host="0.0.0.0", port=port)

# handlers
bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CommandHandler("info", info))
bot_app.add_handler(CommandHandler("list", list_cmd))
bot_app.add_handler(CommandHandler("broadcast", broadcast))
bot_app.add_handler(CallbackQueryHandler(buttons))

if __name__ == "__main__":

    threading.Thread(target=run_web, daemon=True).start()
    threading.Thread(target=auto_loop, daemon=True).start()

    bot_app.run_polling(drop_pending_updates=True)
