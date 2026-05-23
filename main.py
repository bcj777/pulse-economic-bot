import os
import asyncio
import threading
import time
import requests
from flask import Flask
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler

from users_db import init_db, add_user, get_users

TOKEN = os.getenv("BOT_TOKEN")
ADMIN_ID = 2054196564

app = Flask(__name__)
init_db()

bot_app = Application.builder().token(TOKEN).build()

# =========================
# MARKDOWN HELP
# =========================
def fmt(text):
    return text.replace("-", "\-").replace(".", "\.").replace("(", "\(").replace(")", "\)")

# =========================
# START
# =========================
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    chat_id = update.effective_chat.id
    add_user(chat_id)

    keyboard = [
        [InlineKeyboardButton("📅 Calendar", callback_data="calendar")],
        [InlineKeyboardButton("📰 News", callback_data="news")]
    ]

    await update.message.reply_text(
        "*📊 Trading Bot PRO v3 ACTIVE*",
        parse_mode="Markdown",
        reply_markup=InlineKeyboardMarkup(keyboard)
    )

# =========================
# CALENDAR
# =========================
def get_calendar():
    try:
        data = requests.get(
            "https://nfs.faireconomy.media/ff_calendar_thisweek.json",
            timeout=10
        ).json()

        out = []

        for e in data:
            if str(e.get("impact", "")).lower() == "high":
                out.append(f"🔴 {e.get('country')} - {e.get('title')}")

        return "*📅 HIGH IMPACT CALENDAR*\n\n" + "\n".join(out[:10])

    except:
        return "Calendar error"

# =========================
# BUTTONS
# =========================
async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    q = update.callback_query
    await q.answer()

    if q.data == "calendar":
        await q.message.reply_text(get_calendar(), parse_mode="Markdown")

    elif q.data == "news":
        await q.message.reply_text("*📰 News engine active*", parse_mode="Markdown")

# =========================
# BROADCAST (FIXED)
# =========================
async def broadcast(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_ID:
        return

    if not context.args:
        await update.message.reply_text("*Usage:* /broadcast mesaj", parse_mode="Markdown")
        return

    msg = " ".join(context.args)

    users = get_users()
    sent = 0

    for u in users:
        try:
            await bot_app.bot.send_message(
                chat_id=u,
                text=f"*📢 BROADCAST*\n\n_{msg}_",
                parse_mode="Markdown"
            )
            sent += 1
        except:
            pass

    await update.message.reply_text(f"*Sent to:* {sent}", parse_mode="Markdown")

# =========================
# INFO (FIXED)
# =========================
async def info(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.effective_chat.id != ADMIN_ID:
        return

    users = get_users()

    text = "*👥 USERS LIST*\n\n"
    text += f"*Total:* {len(users)}\n\n"

    for u in users[:50]:
        text += f"• `{u}`\n"

    await update.message.reply_text(text, parse_mode="Markdown")

# =========================
# NEWS ENGINE V3 (REAL SCORING)
# =========================
seen = set()

def get_news():
    alerts = []

    try:
        crypto = requests.get(
            "https://api.coingecko.com/api/v3/simple/price?ids=bitcoin,ethereum,solana&vs_currencies=usd&include_24hr_change=true"
        ).json()

        for coin, d in crypto.items():
            change = d.get("usd_24h_change", 0)

            score = abs(change)

            if score >= 3:
                key = f"crypto_{coin}"

                if key not in seen:
                    seen.add(key)

                    alerts.append(
                        f"*🚨 CRYPTO SIGNAL*\n\n_{coin.upper()}_\nChange: *{change:.2f}%*\nScore: *{score:.1f}*"
                    )

        stocks = requests.get(
            "https://query1.finance.yahoo.com/v7/finance/quote?symbols=AAPL,TSLA,NVDA"
        ).json()

        for s in stocks.get("quoteResponse", {}).get("result", []):
            change = s.get("regularMarketChangePercent", 0)
            symbol = s.get("symbol")

            score = abs(change)

            if score >= 2:
                key = f"stock_{symbol}"

                if key not in seen:
                    seen.add(key)

                    alerts.append(
                        f"*🚨 STOCK SIGNAL*\n\n_{symbol}_\nChange: *{change:.2f}%*\nScore: *{score:.1f}*"
                    )

    except:
        pass

    return alerts

# =========================
# SAFE LOOP
# =========================
def news_loop():
    while True:
        news = get_news()

        if news:
            users = get_users()

            async def run():
                for u in users:
                    for n in news:
                        try:
                            await bot_app.bot.send_message(
                                chat_id=u,
                                text=n,
                                parse_mode="Markdown"
                            )
                        except:
                            pass

            asyncio.run(run())

        time.sleep(120)

# =========================
# HANDLERS (FIX IMPORTANT)
# =========================
bot_app.add_handler(CommandHandler("start", start))
bot_app.add_handler(CommandHandler("broadcast", broadcast))
bot_app.add_handler(CommandHandler("info", info))
bot_app.add_handler(CallbackQueryHandler(button))

# =========================
# RUN
# =========================
async def run():
    await bot_app.initialize()
    await bot_app.start()
    await bot_app.updater.start_polling()
    await asyncio.Event().wait()

@app.route("/")
def home():
    return "BOT RUNNING PRO V3"

if __name__ == "__main__":
    threading.Thread(target=lambda: asyncio.run(run())).start()
    threading.Thread(target=news_loop).start()

    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
