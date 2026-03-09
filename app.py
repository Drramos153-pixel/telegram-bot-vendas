import os
import threading
import asyncio
from flask import Flask
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")

app = Flask(__name__)

@app.route("/")
def home():
    return "Servidor online"


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot funcionando!")


async def run_bot():
    tg_app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    tg_app.add_handler(CommandHandler("start", start))

    print("Bot iniciado")
    await tg_app.run_polling()


def start_bot():
    asyncio.run(run_bot())


if __name__ == "__main__":
    threading.Thread(target=start_bot).start()
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
