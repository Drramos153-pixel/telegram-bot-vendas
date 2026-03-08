from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = "8641737018:AAF6DXmD_EIS1FWHNRIgmYnul4VXlPD0zb0"

CANAL_LINK = "https://t.me/+LcqMJ8HuoUxiYjU5"

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Acessar Conteúdo VIP", callback_data="acesso")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "Bem-vindo ao conteúdo VIP.\n\nClique abaixo para acessar:",
        reply_markup=reply_markup
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "acesso":
        await query.message.reply_text(
            f"Entre no canal privado:\n{CANAL_LINK}"
        )

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))

print("Bot iniciado...")

app.run_polling()
