import os
from dotenv import load_dotenv
from telegram.ext import ApplicationBuilder, CommandHandler
from bot.handlers import start, produtos, pedido, status

load_dotenv()

def main():
    token = os.getenv("BOT_TOKEN")
    app = ApplicationBuilder().token(token).build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("produtos", produtos))
    app.add_handler(CommandHandler("pedido", pedido))
    app.add_handler(CommandHandler("status", status))

    print("Bot rodando...")
    app.run_polling()

if __name__ == "__main__":
    main()
