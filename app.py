import os
import threading
import asyncio
import uuid
import time
import sqlite3
import requests
from flask import Flask, request, jsonify
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes, CallbackQueryHandler

TELEGRAM_TOKEN = os.getenv("TELEGRAM_TOKEN")
MP_ACCESS_TOKEN = os.getenv("MP_ACCESS_TOKEN")
CANAL_ID = int(os.getenv("CANAL_ID"))
APP_BASE_URL = os.getenv("APP_BASE_URL")

DB_FILE = "pagamentos.db"
app = Flask(__name__)
tg_app = None


def init_db():
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS pagamentos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_user_id INTEGER NOT NULL,
            payment_id TEXT,
            status TEXT DEFAULT 'pending'
        )
    """)
    conn.commit()
    conn.close()


def salvar_pagamento(user_id: int, payment_id: str):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO pagamentos (telegram_user_id, payment_id, status) VALUES (?, ?, ?)",
        (user_id, payment_id, "pending")
    )
    conn.commit()
    conn.close()


def buscar_usuario_por_payment(payment_id: str):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute(
        "SELECT telegram_user_id FROM pagamentos WHERE payment_id = ?",
        (payment_id,)
    )
    row = cur.fetchone()
    conn.close()
    return row[0] if row else None


def marcar_pago(payment_id: str):
    conn = sqlite3.connect(DB_FILE)
    cur = conn.cursor()
    cur.execute(
        "UPDATE pagamentos SET status = 'approved' WHERE payment_id = ? AND status != 'approved'",
        (payment_id,)
    )
    changed = cur.rowcount
    conn.commit()
    conn.close()
    return changed > 0


@app.route("/")
def home():
    return "Servidor online"


@app.route("/webhook/mercadopago", methods=["POST"])
def webhook_mercadopago():
    data = request.json or {}

    if data.get("type") != "payment":
        return jsonify({"ok": True}), 200

    payment_id = str(data["data"]["id"])

    url = f"https://api.mercadopago.com/v1/payments/{payment_id}"
    headers = {
        "Authorization": f"Bearer {MP_ACCESS_TOKEN}"
    }

    response = requests.get(url, headers=headers, timeout=30)
    pagamento = response.json()

    if pagamento.get("status") == "approved":
        user_id = buscar_usuario_por_payment(payment_id)

        if user_id:
            foi_marcado_agora = marcar_pago(payment_id)

            if foi_marcado_agora:
                expire_date = int(time.time()) + 3600

                invite = asyncio.run(
                    tg_app.bot.create_chat_invite_link(
                        chat_id=CANAL_ID,
                        member_limit=1,
                        expire_date=expire_date,
                        name=f"vip_{user_id}_{payment_id}"
                    )
                )

                asyncio.run(
                    tg_app.bot.send_message(
                        chat_id=user_id,
                        text=(
                            "✅ Pagamento confirmado!\n\n"
                            f"Seu acesso VIP:\n{invite.invite_link}\n\n"
                            "⚠️ Link válido para 1 acesso e expira em 1 hora."
                        )
                    )
                )

    return jsonify({"ok": True}), 200


async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    keyboard = [
        [InlineKeyboardButton("🛒 Comprar acesso VIP", callback_data="comprar")],
        [InlineKeyboardButton("ℹ️ Como funciona", callback_data="info")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    mensagem = (
        "🔥 *ACESSO VIP* 🔥\n\n"
        "Conteúdo exclusivo liberado após pagamento.\n\n"
        "💰 Valor: *R$29,90*\n"
        "🔒 Pagamento único\n\n"
        "Clique no botão abaixo para comprar."
    )

    await update.message.reply_text(
        mensagem,
        reply_markup=reply_markup,
        parse_mode="Markdown"
    )


async def comprar(update: Update, context: ContextTypes.DEFAULT_TYPE):
    if update.callback_query:
        user_id = update.callback_query.from_user.id
        chat = update.callback_query.message
    else:
        user_id = update.effective_user.id
        chat = update.message

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
        "notification_url": f"{APP_BASE_URL}/webhook/mercadopago",
        "payer": {
            "email": f"cliente_{user_id}@example.com",
            "first_name": "Cliente"
        }
    }

    response = requests.post(url, json=body, headers=headers, timeout=30)
    data = response.json()

    if "point_of_interaction" in data:
        payment_id = str(data["id"])
        salvar_pagamento(user_id, payment_id)

        pix_code = data["point_of_interaction"]["transaction_data"]["qr_code"]

        await chat.reply_text(
            "✅ PIX gerado com sucesso.\n\nVou enviar o código copia e cola na próxima mensagem."
        )

        await chat.reply_text(pix_code)

        await chat.reply_text(
            "Assim que o pagamento for aprovado, o link VIP será enviado automaticamente."
        )
    else:
        await chat.reply_text(f"Erro ao gerar PIX:\n{data}")


async def botoes(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    if query.data == "comprar":
        await comprar(update, context)

    elif query.data == "info":
        await query.message.reply_text(
            "📌 Como funciona:\n\n"
            "1️⃣ Clique em comprar\n"
            "2️⃣ Pague o PIX gerado\n"
            "3️⃣ Após o pagamento, você recebe automaticamente o acesso VIP."
        )


async def bot_main():
    global tg_app
    tg_app = ApplicationBuilder().token(TELEGRAM_TOKEN).build()
    tg_app.add_handler(CommandHandler("start", start))
    tg_app.add_handler(CommandHandler("comprar", comprar))
    tg_app.add_handler(CallbackQueryHandler(botoes))

    print("Bot iniciado")
    await tg_app.initialize()
    await tg_app.start()
    await tg_app.updater.start_polling()

    while True:
        await asyncio.sleep(3600)


def run_bot():
    asyncio.run(bot_main())


if __name__ == "__main__":
    init_db()
    threading.Thread(target=run_bot, daemon=True).start()
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)
