from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

TOKEN = "8641737018:AAF6DXmD_EIS1FWHNRIgmYnul4VXlPD0zb0"

async def start(update, context: ContextTypes.DEFAULT_TYPE):
    await update.message.reply_text("Bot funcionando!")

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))

print("Bot iniciado...")
app.run_polling()
