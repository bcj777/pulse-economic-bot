import os
import threading
import requests
import time
from flask import Flask

from telegram import (
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup
)

from telegram.ext import (
    Application,
    CommandHandler,
    CallbackQueryHandler,
    ContextTypes
)

from users_db import (
    init_db,
    add_user,
    get_users
)

# =====================
# CONFIG
# =====================
TOKEN = os.getenv("BOT_TOKEN")
FINNHUB_KEY = os.getenv("FINNHUB_KEY")

ADMIN_ID = 2054196564

init_db()

# =====================
# FLASK WEB SERVER
# =====================
web = Flask(__name__)

@web.route("/")
def home():
    return "BOT ONLINE"

# =====================
# TELEGRAM APP
# =====================
bot_app = Application.builder().token(TOKEN).build()

seen_news = set()

KEYWORDS = {
    "fed": 3,
    "inflation": 3,
    "cpi": 3,
    "nfp": 3,
    "rate": 3,
    "bitcoin": 2,
    "crypto": 2,
    "usd": 2,
    "stocks": 2,
    "recession": 3
}


# =====================
# SCORE SYSTEM
# =====================
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
        url = (
            f"https://finnhub.io/api/v1/news"
            f"?category=general&token={FINNHUB_KEY}"
        )

        data = requests.get(url, timeout=10).json()

        alerts = []

        for n in data[:15]:
            title = n.get("headline", "")

            if title in seen_news:
                continue

            seen_news.add(title)

            if score(title) >= 3:
                alerts.append(
                    f"🚨 <b>HIGH IMPACT NEWS</b>\n\n{title}"
                )

        return alerts

    except:
        return []


# =====================
# CALENDAR ENGINE
# =====================
def fetch_calendar():
    try:
        url = (
            f"https://finnhub.io/api/v1/calendar/economic"
            f"?token={FINNHUB_KEY}"
        )

        data = requests.get(url, timeout=10).json()

        events = data.get(
            "economicCalendar",
            []
        )

        out = []

        for e in events:
            impact = str(
                e.get("impact", "")
            ).lower()

            if "high" in impact:
                out.append(
                    f"📅 <b>HIGH IMPACT</b>\n\n"
                    f"{e.get('date')} {e.get('time')}\n"
                    f"{e.get('event')}\n"
                    f"{e.get('country')}"
                )

        if not out:
            return (
                "📅 <b>No high impact events today.</b>"
            )

        return "\n\n━━━━━━━━━━\n\n".join(out)

    except:
        return "Calendar error"


# =====================
# START
# =====================
async def start(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    user_id = update.effective_user.id
    add_user(user_id)

    keyboard = [
        [
            InlineKeyboardButton(
                "📅 Economic Calendar",
                callback_data="calendar"
            )
        ],
        [
            InlineKeyboardButton(
                "📰 News",
                callback_data="news"
            )
        ]
    ]

    if user_id == ADMIN_ID:
        keyboard.append(
            [
                InlineKeyboardButton(
                    "⚙️ Admin Panel",
                    callback_data="admin"
                )
            ]
        )

    await update.message.reply_text(
        "<b>🚀 TRADING ENGINE ACTIVE</b>",
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup(
            keyboard
        )
    )
