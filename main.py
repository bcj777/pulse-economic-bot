import os
import requests
import time
import threading

from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

from users_db import init_db, add_user, get_users

# =====================
# CONFIG
# =====================
TOKEN = os.getenv("BOT_TOKEN")
FINNHUB_KEY = os.getenv("FINNHUB_KEY")
ADMIN_ID = 2054196564

init_db()

app = Application.builder().token(TOKEN).build()

# =====================
# USERS TRACKING
# =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_user.id
    add_user(user_id)

    keyboard = [
        [InlineKeyboardButton("📅 Calendar", callback_data="calendar")],
        [InlineKeyboardButton("📰 News", callback_data="news")]
    ]

    if user_id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("⚙️ Admin", callback_data="admin")])

    await update.message.reply_text(
        "🚀 ENGINE V2 ACTIVE",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# =====================
# SCORE ENGINE
# =====================
KEYWORDS = {
    "fed": 3,
    "inflation": 3,
    "cpi": 3,
    "nfp": 3,
    "rate": 3,
    "bitcoin": 2,
    "crypto": 2,
    "usd": 2,
    "stocks": 2
}

seen_news = set()


def score(text):
    text = text.lower()
    s = 0

    for k, v in KEYWORDS.items():
        if k in text:
            s += v

    return s


# =====================
# NEWS ENGINE
# =====================
def fetch_news():
    try:
        url = f"https://finnhub.io/api/v1/news?category=general&token={FINNHUB_KEY}"
        data = requests.get(url, timeout=10).json()

        alerts = []

        for n in data[:15]:
            title = n.get("headline", "")

            if title in seen_news:
                continue

            seen_news.add(title)

            if score(title) >= 3:
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

        if not out:
            return "No high impact events today."

        return "\n━━━━━━━━━━\n".join(out)

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
        users = get_users()
        await q.message.reply_text(f"👥 Users: {len(users)}")


# =====================
# AUTO ENGINE LOOP (SAFE)
# =====================
def auto_loop():
    while True:
        try:
            news = fetch_news()
            users = get_users()

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
# HANDLERS
# =====================
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(buttons))

# =====================
# START
# =====================
if __name__ == "__main__":
    print("ENGINE V2 STARTED")

    threading.Thread(target=auto_loop, daemon=True).start()

    app.run_polling()
