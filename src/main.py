import logging
from telegram.ext import Application, MessageHandler, CallbackQueryHandler, filters
from config import Config
from bot import handle_message, handle_callback

logging.basicConfig(
    format="%(asctime)s %(levelname)s %(name)s: %(message)s",
    level=logging.INFO,
)
logger = logging.getLogger(__name__)


def main() -> None:
    app = Application.builder().token(Config.TELEGRAM_BOT_TOKEN).build()

    # Handle text messages (bot sees these when mentioned or replied to in groups)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_message))

    # Handle inline button presses (Tier 2 approvals)
    app.add_handler(CallbackQueryHandler(handle_callback))

    logger.info("Mora Tech Bot starting...")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
