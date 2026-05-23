import os
import asyncio
from telegram import Update
from telegram.ext import Application, CommandHandler, ContextTypes

TOKEN = os.getenv("BOT_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Salut! Bot activ 🤖")

async def main():
    app = Application.builder().token(TOKEN).build()

    app.add_handler(CommandHandler("start", start))

    print("Bot pornit...")

    await app.initialize()
    await app.start()
    await app.updater.start_polling()

    # ține procesul activ
    await asyncio.Event().wait()

if __name__ == "__main__":
    asyncio.run(main())
