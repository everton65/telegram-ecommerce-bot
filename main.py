import os
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, CommandHandler, CallbackQueryHandler, MessageHandler, filters
from bot.handlers import start, produtos, pedido, status, promocoes, buscar, admin, ranking, ajuda, menu_handler, button_handler

load_dotenv()

def main():
    token = os.getenv("BOT_TOKEN")
    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("produtos", produtos))
    app.add_handler(CommandHandler("produto", pedido))
    app.add_handler(CommandHandler("status", status))
    app.add_handler(CommandHandler("promocoes", promocoes))
    app.add_handler(CommandHandler("buscar", buscar))
    app.add_handler(CommandHandler("admin", admin))
    app.add_handler(CommandHandler("ranking", ranking))
    app.add_handler(CommandHandler("ajuda", ajuda))

    app.add_handler(CallbackQueryHandler(button_handler))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, menu_handler))

    print("Bot rodando...")
    app.run_polling()

if __name__ == "__main__":
    main()