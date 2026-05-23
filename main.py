import os
import asyncio
from flask import Flask
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

app = Flask(__name__)

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Salut! Bot activ 🤖")

async def run_bot():
    application = Application.builder().token(TOKEN).build()
    application.add_handler(CommandHandler("start", start))

    await application.initialize()
    await application.start()
    await application.updater.start_polling()

    await asyncio.Event().wait()

@app.route("/")
def home():
    return "OK"

if __name__ == "__main__":
    import threading

    # pornim botul în background
    threading.Thread(target=lambda: asyncio.run(run_bot())).start()

    # IMPORTANT: asta ține Render alive
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
