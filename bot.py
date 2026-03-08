from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, ChatJoinRequestHandler, ContextTypes
import time

TOKEN = "SEU_TOKEN_AQUI"

CANAL_ID = -1003699760336
VALOR = "R$ 29,90"

autorizados = set()

async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):

    keyboard = [
        [InlineKeyboardButton(f"Comprar acesso - {VALOR}", callback_data="comprar")]
    ]

    reply_markup = InlineKeyboardMarkup(keyboard)

    await update.message.reply_text(
        f"🔥 Conteúdo VIP\n\nAcesso único: {VALOR}",
        reply_markup=reply_markup
    )

async def button(update: Update, context: ContextTypes.DEFAULT_TYPE):

    query = update.callback_query
    await query.answer()

    user_id = query.from_user.id

    if query.data == "comprar":

        autorizados.add(user_id)

        expire_date = int(time.time()) + 900

        invite = await context.bot.create_chat_invite_link(
            chat_id=CANAL_ID,
            name=f"compra_{user_id}",
            expire_date=expire_date,
            creates_join_request=True
        )

        await query.message.reply_text(
            "✅ Compra registrada\n\n"
            "Seu link exclusivo:\n\n"
            f"{invite.invite_link}\n\n"
            "⚠️ Expira em 15 minutos"
        )

async def handle_join_request(update: Update, context: ContextTypes.DEFAULT_TYPE):

    req = update.chat_join_request
    user_id = req.from_user.id

    if user_id in autorizados:

        await context.bot.approve_chat_join_request(
            chat_id=req.chat.id,
            user_id=user_id
        )

        autorizados.remove(user_id)

    else:

        await context.bot.decline_chat_join_request(
            chat_id=req.chat.id,
            user_id=user_id
        )

app = ApplicationBuilder().token(TOKEN).build()

app.add_handler(CommandHandler("start", start))
app.add_handler(CallbackQueryHandler(button))
app.add_handler(ChatJoinRequestHandler(handle_join_request))

print("Bot iniciado...")

app.run_polling()
