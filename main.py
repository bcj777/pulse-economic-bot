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
from datetime import datetime, timezone


def fetch_news():

    try:
        url = (
            f"https://finnhub.io/api/v1/news"
            f"?category=general&token={FINNHUB_KEY}"
        )

        data = requests.get(
            url,
            timeout=10
        ).json()

        recent_news = []
        auto_alerts = []

        now = datetime.now(
            timezone.utc
        ).timestamp()

        for n in data:

            title = n.get(
                "headline",
                ""
            )

            summary = n.get(
                "summary",
                ""
            )

            ts = n.get(
                "datetime",
                0
            )

            # 24h filter
            if now - ts > 86400:
                continue

            text = (
                title + " " + summary
            )

            s = score(text)

            if s >= 3:

                msg = (
                    f"📰 <b>HIGH IMPACT</b>\n\n"
                    f"{title}"
                )

                # NEWS BUTTON LIST
                recent_news.append(msg)

                # AUTO ALERTS
                if title not in seen_news:
                    seen_news.add(title)
                    auto_alerts.append(msg)

        # limit la 10
        recent_news = recent_news[:10]

        return (
            recent_news,
            auto_alerts
        )

    except:
        return [], []

# =====================
# CALENDAR ENGINE
# =====================
from datetime import datetime


def fetch_calendar():
    try:
        today = datetime.utcnow().strftime("%Y-%m-%d")

        url = (
            f"https://finnhub.io/api/v1/calendar/economic"
            f"?token={FINNHUB_KEY}"
        )

        data = requests.get(
            url,
            timeout=10
        ).json()

        events = data.get(
            "economicCalendar",
            []
        )

        out = []

        for e in events:

            event_date = str(
                e.get("date", "")
            )

            impact = str(
                e.get("impact", "")
            ).lower()

            # TODAY + HIGH ONLY
            if (
                event_date == today
                and "high" in impact
            ):

                out.append(
                    f"📅 <b>HIGH IMPACT</b>\n\n"
                    f"🕒 {e.get('time')}\n"
                    f"🌍 {e.get('country')}\n"
                    f"📊 {e.get('event')}"
                )

        if not out:
            return (
                "📅 <b>No high impact events today.</b>"
            )

        return "\n\n━━━━━━━━━━\n\n".join(out)

    except Exception as e:
        return f"Calendar error: {e}"

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
        _, news = fetch_news() 

        elif q.data == "news":

    recent, _ = fetch_news()

    if not recent:
        await q.message.reply_text(
            "📰 <b>No recent high impact news.</b>",
            parse_mode="HTML"
        )

    else:
        await q.message.reply_text(
            "\n\n━━━━━━━━━━\n\n".join(
                recent
            ),
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
# AUTO CALENDAR 7AM
# =====================
last_calendar_day = None

def auto_calendar_loop():
    global last_calendar_day

    while True:
        try:
            now = datetime.now()

            # 07:00 local server
            if (
                now.hour == 4
                and now.minute == 0
            ):

                today = now.strftime(
                    "%Y-%m-%d"
                )

                if last_calendar_day != today:

                    msg = fetch_calendar()

                    users = get_users()

                    for u in users:
                        try:
                            bot_app.bot.send_message(
                                chat_id=u,
                                text=(
                                    "📅 <b>DAILY ECONOMIC CALENDAR</b>\n\n"
                                    + msg
                                ),
                                parse_mode="HTML"
                            )
                        except:
                            pass

                    last_calendar_day = today

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
# FLASK THREAD
# =====================
def run_web():
    port = int(os.environ.get("PORT", 10000))

    web.run(
        host="0.0.0.0",
        port=port
    )


# =====================
# MAIN
# =====================
if __name__ == "__main__":

    threading.Thread(
        target=run_web,
        daemon=True
    ).start()

    threading.Thread(
        target=auto_news_loop,
        daemon=True
    ).start()

    threading.Thread(
    target=auto_calendar_loop,
    daemon=True
).start()

    print("BOT POLLING STARTED")

    bot_app.run_polling(
        drop_pending_updates=True
    )

   
