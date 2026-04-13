import logging
from telegram import Bot
from config import Config

logger = logging.getLogger(__name__)


async def notify_maleesha(bot: Bot, message: str) -> None:
    try:
        await bot.send_message(
            chat_id=Config.MALEESHA_CHAT_ID,
            text=message,
            parse_mode="HTML",
        )
    except Exception as e:
        logger.error(f"Failed to notify Maleesha: {e}")


def format_escalation(
    reporter: str,
    original_message: str,
    diagnosis: str,
    recommended_step: str,
    chat_id: int,
) -> str:
    return (
        f"<b>ESCALATION — Tech Issue</b>\n\n"
        f"Reported by: {reporter}\n"
        f"Group: {chat_id}\n\n"
        f"Staff said: <i>{original_message}</i>\n\n"
        f"<b>Diagnosis:</b>\n{diagnosis}\n\n"
        f"<b>Recommended next step:</b>\n{recommended_step}"
    )
