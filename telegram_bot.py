"""Telegram bot for controlling the cat projector toy remotely.
Uses long polling — no ngrok or public URL needed. Just run it on the Pi.

Setup:
1. Open Telegram, search for @BotFather
2. Send /newbot, name it something like "Cat Projector"
3. Copy the token and put it in config.py or set TELEGRAM_BOT_TOKEN env var
4. Run: python telegram_bot.py
5. Open the bot in Telegram and send "on" or "off"
"""
import logging
import os
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes
import playback_controller
import config

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(name)s] %(message)s",
)
log = logging.getLogger("telegram_bot")

# Optional: restrict to specific Telegram user IDs for security
# Find your ID by sending /start and checking the logs
ALLOWED_USER_IDS = []  # empty = allow anyone


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle plain text messages: on, off, status."""
    if not update.message or not update.message.text:
        return

    user_id = update.effective_user.id
    username = update.effective_user.username or "unknown"

    if ALLOWED_USER_IDS and user_id not in ALLOWED_USER_IDS:
        log.info(f"Rejected message from unauthorized user: {user_id} ({username})")
        await update.message.reply_text("🚫 Unauthorized.")
        return

    command = update.message.text.strip().lower()
    log.info(f"Message from {username} ({user_id}): {command}")

    if command in ("on", "start", "play"):
        success, response = playback_controller.start_playback("koi_preview")
        await update.message.reply_text(f"🐟 {response}")

    elif command in ("off", "stop"):
        success, response = playback_controller.stop_playback()
        await update.message.reply_text(f"⏹️ {response}")

    elif command == "status":
        status = playback_controller.get_status()
        await update.message.reply_text(f"📊 {status}")

    elif command in ("help", "?"):
        await update.message.reply_text(
            "🐱 Cat Projector Commands:\n"
            "• on — Start fish animation\n"
            "• off — Stop playback\n"
            "• status — Check what's playing"
        )

    else:
        await update.message.reply_text(
            f"🐱 Unknown command '{command}'. Send 'help' for options."
        )


async def command_start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle /start command (when user first opens the bot)."""
    user_id = update.effective_user.id
    username = update.effective_user.username or "unknown"
    log.info(f"New user: {username} (ID: {user_id})")
    await update.message.reply_text(
        "🐱 Cat Projector Bot\n\n"
        "Send 'on' to start the fish, 'off' to stop.\n\n"
        f"Your user ID: {user_id} (add to ALLOWED_USER_IDS for security)"
    )


def main():
    token = os.environ.get("TELEGRAM_BOT_TOKEN", config.TELEGRAM_BOT_TOKEN)

    if not token or token == "YOUR_TELEGRAM_BOT_TOKEN":
        print("=" * 50)
        print("ERROR: No Telegram bot token set!")
        print()
        print("1. Open Telegram, search for @BotFather")
        print("2. Send /newbot and follow the prompts")
        print("3. Copy the token")
        print("4. Set it in config.py (TELEGRAM_BOT_TOKEN)")
        print("   or as env var: TELEGRAM_BOT_TOKEN=your_token")
        print("=" * 50)
        return

    print("=" * 50)
    print("🐱 Cat Projector — Telegram Bot")
    print("=" * 50)
    print(f"Bot token: {token[:8]}...{token[-4:]}")
    print("Listening for messages (long polling)...")
    print("Send 'on' or 'off' to your bot in Telegram.")
    print("=" * 50)

    application = Application.builder().token(token).build()
    application.add_handler(CommandHandler("start", command_start))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    application.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
