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
