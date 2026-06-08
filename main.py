import os
import asyncio
import logging
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, MessageHandler, filters, ContextTypes
from bot.handlers.ai_chat import ai_chat_handler  # Imports your AI reply engine file

# Set up logging to monitor server status directly in your Render panel logs
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Sends an introductory greeting statement when the bot is initialized via the /start command."""
    # Check if the message actually exists before replying to it
    if update.message:
        await update.message.reply_text("🤖 Hello! I am your 24/7 Group Manager and AI Companion bot. Make me an admin to access my tools!")

def main():
    # Securely fetch the API environment token variable compiled via Render Dashboard
    token = os.environ.get("TELEGRAM_TOKEN")
    if not token:
        raise ValueError("CRITICAL: TELEGRAM_TOKEN environment variable is missing on the server backend configuration dashboard!")

    # Initialize the background bot framework application instance loop
    app = ApplicationBuilder().token(token).build()

    # Register core operational signal listener routes
    app.add_handler(CommandHandler("start", start_command))

    # Directs all message traffic and direct message replies into your custom Gemini script
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_chat_handler))

    print("🚀 Bot process sequence starting loop... listening to Telegram endpoints cleanly!")
    app.run_polling()

if __name__ == '__main__':
    main()
