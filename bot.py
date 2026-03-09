import os
import uuid
import requests
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ContextTypes

TOKEN = os.getenv("TELEGRAM_TOKEN")
MP_ACCESS_TOKEN = os.getenv("MP_ACCESS_TOKEN")

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("Comprar acesso VIP - R$29,90", callback_data="comprar")]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        "🔥 Acesso VIP 🔥\n\nClique abaixo para comprar acesso por R$29,90.",
        reply_markup=reply_markup
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "comprar":
        url = "https://api.mercadopago.com/v1/payments"
        headers = {
            "Authorization": f"Bearer {MP_ACCESS_TOKEN}",
            "Content-Type": "application/json",
            "X-Idempotency-Key": str(uuid.uuid4())
        }
        body = {
            "transaction_amount": 29.90,
            "description": "Acesso VIP Telegram",
            "payment_method_id": "pix",
            "payer": {
                "email": "cliente@example.com",
                "first_name": "Cliente"
            }
        }

        response = requests.post(url, json=body, headers=headers)
        data = response.json()

        if "point_of_interaction" in data:
            pix_code = data["point_of_interaction"]["transaction_data"]["qr_code"]
            await query.message.reply_text(
                f"✅ PIX gerado com sucesso.\n\nCopie e pague o código abaixo:\n\n{pix_code}"
            )
        else:
            await query.message.reply_text(
                f"Erro ao gerar PIX:\n{data}"
            )

app = ApplicationBuilder().token(TOKEN).build()
app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))

print("Bot iniciado")
app.run_polling()
