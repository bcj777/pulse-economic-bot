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


# =====================
# CALLBACKS
# =====================
async def buttons(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    q = update.callback_query
    await q.answer()

    # CALENDAR
    if q.data == "calendar":
        await q.message.reply_text(
            fetch_calendar(),
            parse_mode="HTML"
        )

    # NEWS
    elif q.data == "news":
        news = fetch_news()

        if not news:
            await q.message.reply_text(
                "📰 <b>No high impact news.</b>",
                parse_mode="HTML"
            )
        else:
            await q.message.reply_text(
                "\n\n".join(news),
                parse_mode="HTML"
            )

    # ADMIN
    elif q.data == "admin":
        if q.from_user.id == ADMIN_ID:
            users = get_users()

            await q.message.reply_text(
                f"⚙️ <b>ADMIN PANEL</b>\n\n"
                f"👥 Users: {len(users)}",
                parse_mode="HTML"
            )


# =====================
# ADMIN COMMANDS
# =====================
async def info(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_user.id != ADMIN_ID:
        return

    users = get_users()

    await update.message.reply_text(
        f"👥 Users: {len(users)}",
        parse_mode="HTML"
    )


async def list_cmd(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_user.id != ADMIN_ID:
        return

    await update.message.reply_text(
        "/info\n"
        "/broadcast mesaj\n"
        "/list",
        parse_mode="HTML"
    )


async def broadcast(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE
):
    if update.effective_user.id != ADMIN_ID:
        return

    if not context.args:
        return await update.message.reply_text(
            "Usage:\n/broadcast mesaj"
        )

    msg = " ".join(context.args)

    users = get_users()
    sent = 0

    for u in users:
        try:
            await bot_app.bot.send_message(
                chat_id=u,
                text=f"📢 {msg}",
                parse_mode="HTML"
            )
            sent += 1
        except:
            pass

    await update.message.reply_text(
        f"Sent: {sent}"
    )


# =====================
# AUTO NEWS LOOP
# =====================
def auto_news_loop():
    while True:
        try:
            news = fetch_news()

            if news:
                users = get_users()

                for u in users:
                    for n in news:
                        try:
                            bot_app.bot.send_message(
                                chat_id=u,
                                text=n,
                                parse_mode="HTML"
                            )
                        except:
                            pass

            time.sleep(60)

        except:
            time.sleep(60)


# =====================
# HANDLERS
# =====================
bot_app.add_handler(
    CommandHandler(
        "start",
        start
    )
)

bot_app.add_handler(
    CommandHandler(
        "info",
        info
    )
)

bot_app.add_handler(
    CommandHandler(
        "list",
        list_cmd
    )
)

bot_app.add_handler(
    CommandHandler(
        "broadcast",
        broadcast
    )
)

bot_app.add_handler(
    CallbackQueryHandler(
        buttons
    )
)


# =====================
# BOT THREAD
# =====================
def run_bot():
    bot_app.run_polling(
        drop_pending_updates=True
    )


# =====================
# MAIN
# =====================
if __name__ == "__main__":
    threading.Thread(
        target=run_bot,
        daemon=True
    ).start()

    threading.Thread(
        target=auto_news_loop,
        daemon=True
    ).start()

    port = int(
        os.environ.get(
            "PORT",
            10000
        )
    )

    web.run(
        host="0.0.0.0",
        port=port
    )
