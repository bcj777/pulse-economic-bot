import os
import requests
from datetime import datetime

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

bot_app = Application.builder().token(TOKEN).build()

# =====================
# START
# =====================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user_id = update.effective_chat.id
    add_user(user_id)

    keyboard = [
        [InlineKeyboardButton("📅 Economic Calendar", callback_data="calendar")],
        [InlineKeyboardButton("📰 Market News", callback_data="news")]
    ]

    if user_id == ADMIN_ID:
        keyboard.append([InlineKeyboardButton("⚙️ Admin Panel", callback_data="panel")])

    await update.message.reply_text(
        "━━━━━━━━━━━━━━\n"
        "📊 TRADING BOT ACTIVE\n"
        "━━━━━━━━━━━━━━",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# =====================
# CALENDAR (TODAY ONLY)
# =====================
def get_calendar():
    try:
        url = f"https://finnhub.io/api/v1/calendar/economic?token={FINNHUB_KEY}"
        data = requests.get(url, timeout=10).json()

        events = data.get("economicCalendar", [])
        today = datetime.utcnow().date().isoformat()

        today_events = [
            e for e in events
            if e.get("date", "")[:10] == today
        ]

        if not today_events:
            return "📅 No economic events today."

        out = ["📅 TODAY EVENTS\n━━━━━━━━━━━━━━"]

        for e in today_events:
            out.append(
                f"🗓 {e.get('date')} {e.get('time')}\n"
                f"📊 {e.get('event')}\n"
                f"🌍 {e.get('country')} | 🔥 {e.get('impact')}\n"
                "━━━━━━━━━━━━━━"
            )

        return "\n".join(out)

    except:
        return "Calendar error"

# =====================
# NEWS ENGINE
# =====================
seen = set()

def get_news():
    alerts = []

    try:
        url = f"https://finnhub.io/api/v1/news?category=general&token={FINNHUB_KEY}"
        data = requests.get(url, timeout=10).json()

        keywords = ["fed", "inflation", "rate", "cpi", "nfp", "stock", "crypto"]

        for item in data[:10]:
            headline = item.get("headline", "")

            if headline in seen:
                continue

            seen.add(headline)

            if any(k in headline.lower() for k in keywords):
                alerts.append(
                    "🚨 MARKET NEWS\n━━━━━━━━━━━━━━\n\n"
                    + headline
                )

    except:
        pass

    return alerts

# =====================
# CALLBACK HANDLER
# =====================
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    user_id = q.from_user.id

    if q.data == "calendar":
        await q.message.reply_text(get_calendar())

    elif q.data == "news":
        await q.message.reply_text("📰 News engine active")

    elif q.data == "panel" and user_id == ADMIN_ID:
        keyboard = [
            [InlineKeyboardButton("👥 Users", callback_data="admin_users")],
            [InlineKeyboardButton("📋 Commands", callback_data="admin_list")],
            [InlineKeyboardButton("📊 Status", callback_data="admin_status")]
        ]

        await q.message.reply_text(
            "⚙️ ADMIN PANEL",
            reply_markup=InlineKeyboardMarkup(keyboard)
        )

    elif q.data == "admin_users" and user_id == ADMIN_ID:
        users = get_users()
        await q.message.reply_text(f"Users: {len(users)}")

    elif q.data == "admin_list" and user_id == ADMIN_ID:
        await q.message.reply_text("/start /info /broadcast")

    elif q.data == "admin_status" and user_id == ADMIN_ID:
        await q.message.reply_text("SYSTEM ONLINE")

# =====================
# INFO
# =====================
async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_ID:
        return

    users = get_users()
    await update.message.reply_text(f"Users: {len(users)}")

# =====================
# BROADCAST
# =====================
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_ID:
        return

    msg = " ".join(context.args)
    users = get_users()

    sent = 0

    for u in users:
        try:
            await bot_app.bot.send_message(chat_id=u, text=f"📢 {msg}")
            sent += 1
        except:
            pass

    await update.message.reply_text(f"Sent: {sent}")

# =====================
# REGISTER HANDLERS
# =====================
bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CommandHandler("info", info))
bot_app.add_handler(CommandHandler("broadcast", broadcast))
bot_app.add_handler(CallbackQueryHandler(button))

# =====================
# RUN (CRITICAL FIX)
# =====================
if __name__ == "__main__":
    bot_app.run_polling()
