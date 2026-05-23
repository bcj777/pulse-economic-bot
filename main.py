import os
from flask import Flask, request
from telegram import Update, Bot
from telegram.ext import Application, CommandHandler, ContextTypes

# ===== TOKEN (din Render Environment Variables) =====
TOKEN = os.getenv("BOT_TOKEN")

# ===== FLASK APP =====
app = Flask(__name__)

# ===== TELEGRAM BOT =====
bot = Bot(token=TOKEN)
application = Application.builder().bot(bot).build()

# ===== COMMANDS =====
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Salut! Bot activ 🤖")

application.add_handler(CommandHandler("start", start))

# ===== ROUTES =====
@app.route("/", methods=["GET"])
def home():
    return "OK"

@app.route("/webhook", methods=["POST"])
def webhook():
    data = request.get_json(force=True)
    update = Update.de_json(data, bot)

    application.create_task(application.process_update(update))
    return "ok"

# ===== START SERVER =====
if __name__ == "__main__":
    port = int(os.environ.get("PORT", 10000))
    app.run(host="0.0.0.0", port=port)
