import os
import threading
import time
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

# =====================
# WEB SERVER
# =====================
web = Flask(__name__)

@web.route("/")
def home():
    return "ENGINE WEB PRO ACTIVE ✔"

# =====================
# TELEGRAM BOT
# =====================
app = Application.builder().token(TOKEN).build()

# =====================
# USERS MEMORY
# =====================
users = set()

# =====================
# START
# =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    users.add(update.effective_user.id)

    keyboard = [
        [InlineKeyboardButton("📅 Calendar", callback_data="calendar")],
        [InlineKeyboardButton("📰 News", callback_data="news")]
    ]

    if update.effective_user.id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("⚙️ Admin", callback_data="admin")])

    await update.message.reply_text(
        "🚀 ENGINE WEB PRO ONLINE",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# =====================
# NEWS ENGINE (REAL)
# =====================
seen_news = set()

def fetch_news():
    try:
        url = f"https://finnhub.io/api/v1/news?category=general&token={FINNHUB_KEY}"
        data = requests.get(url, timeout=10).json()

        alerts = []

        keywords = ["fed", "inflation", "cpi", "nfp", "rate", "bitcoin", "crypto", "stock"]

        for n in data[:15]:
            title = n.get("headline", "")

            if title in seen_news:
                continue

            seen_news.add(title)

            if any(k in title.lower() for k in keywords):
                alerts.append("🚨 HIGH IMPACT NEWS\n" + title)

        return alerts

    except:
        return []

# =====================
# CALENDAR ENGINE
# =====================
def fetch_calendar():
    try:
        url = f"https://finnhub.io/api/v1/calendar/economic?token={FINNHUB_KEY}"
        data = requests.get(url, timeout=10).json()

        events = data.get("economicCalendar", [])

        out = []

        for e in events:
            if "high" in str(e.get("impact", "")).lower():
                out.append(
                    f"📅 HIGH IMPACT\n"
                    f"{e.get('date')} {e.get('time')}\n"
                    f"{e.get('event')}\n"
                    f"{e.get('country')} | {e.get('impact')}"
                )

        return "\n━━━━━━━━━━\n".join(out) if out else "No high impact events."

    except:
        return "Calendar error"

# =====================
# CALLBACKS
# =====================
async def buttons(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.data == "calendar":
        await q.message.reply_text(fetch_calendar())

    elif q.data == "news":
        news = fetch_news()

        if not news:
            await q.message.reply_text("No high impact news.")
        else:
            await q.message.reply_text("\n\n".join(news))

    elif q.data == "admin":
        await q.message.reply_text(f"👥 USERS: {len(users)}")

# =====================
# AUTO ENGINE LOOP (SAFE 24/7)
# =====================
def auto_engine():
    while True:
        try:
            news = fetch_news()

            if news:
                for u in users:
                    for n in news:
                        try:
                            app.bot.send_message(chat_id=u, text=n)
                        except:
                            pass

            time.sleep(60)

        except:
            time.sleep(60)

# =====================
# BOT START
# =====================
def run_bot():
    print("BOT STARTED")

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CallbackQueryHandler(buttons))

    app.run_polling()

# =====================
# MAIN RUN
# =====================
if __name__ == "__main__":
    threading.Thread(target=run_bot, daemon=True).start()

    threading.Thread(target=auto_engine, daemon=True).start()

    port = int(os.environ.get("PORT", 10000))
    web.run(host="0.0.0.0", port=port)
