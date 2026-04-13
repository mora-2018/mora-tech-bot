import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from config import Config
from agent import run_agent_loop
from context import get_context, clear_context
from safety import RequiresApprovalError
from escalation import notify_maleesha

logger = logging.getLogger(__name__)


async def handle_message(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not update.message or not update.message.text:
        return

    chat_id = update.effective_chat.id
    user = update.effective_user
    text = update.message.text.strip()

    # Gate 1: approved chat
    if chat_id not in Config.ALLOWED_CHAT_IDS:
        return

    # Gate 2: approved user (if whitelist is configured)
    if Config.ALLOWED_USER_IDS and user.id not in Config.ALLOWED_USER_IDS:
        return

    # Strip bot mention
    bot_username = (await context.bot.get_me()).username
    if text.lower().startswith(f"@{bot_username.lower()}"):
        text = text[len(f"@{bot_username}"):].strip()

    if not text:
        return

    sender = user.first_name or user.username or str(user.id)
    logger.info(f"Message from {sender} ({user.id}) in {chat_id}: {text[:80]}")

    conv_context = get_context(chat_id)

    # Gate 3: circuit breaker
    if conv_context.is_circuit_open():
        await update.message.reply_text(
            "I've hit repeated errors in this chat. Maleesha has been notified. "
            "I'll resume automatically in 10 minutes."
        )
        return

    # Gate 4: rate limit
    allowed, reset_in = conv_context.check_rate_limit()
    if not allowed:
        mins = (reset_in // 60) + 1
        await update.message.reply_text(
            f"Too many requests. Limit is 5 messages per hour. "
            f"Try again in {mins} minute(s)."
        )
        return

    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    try:
        response = await run_agent_loop(text, conv_context)
        await update.message.reply_text(response, parse_mode="HTML")

    except RequiresApprovalError as e:
        keyboard = [[
            InlineKeyboardButton("Approve", callback_data=e.approve_key()),
            InlineKeyboardButton("Cancel", callback_data=e.cancel_key()),
        ]]
        await update.message.reply_text(
            e.approval_message(),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )

    except Exception as e:
        logger.exception(f"Agent crash handling: {text}")

        # Circuit breaker: record crash, notify Maleesha if it just opened
        just_opened = conv_context.record_crash()

        await update.message.reply_text(
            "Something went wrong on my end. Notifying Maleesha."
        )
        msg = (
            f"<b>Tech bot crashed</b>\n\n"
            f"Chat: {chat_id} | User: {sender} ({user.id})\n"
            f"Message: {text[:200]}\n"
            f"Error: {str(e)[:300]}"
        )
        if just_opened:
            msg += f"\n\n<b>Circuit breaker opened for chat {chat_id}. Bot paused for 10 min.</b>"

        await notify_maleesha(context.bot, msg)


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat_id
    user = query.from_user
    data = query.data or ""

    if chat_id not in Config.ALLOWED_CHAT_IDS:
        return

    conv_context = get_context(chat_id)

    if data.startswith("approve:"):
        token = data[len("approve:"):]
        if not conv_context.grant_approval(token):
            await query.edit_message_text("This approval has expired or was already used.")
            return

        await query.edit_message_text(
            query.message.text + f"\n\n<b>Approved by {user.first_name}</b>",
            parse_mode="HTML",
        )
        await context.bot.send_chat_action(chat_id=chat_id, action="typing")
        try:
            response = await run_agent_loop("__resume__", conv_context)
            await context.bot.send_message(chat_id=chat_id, text=response, parse_mode="HTML")
        except Exception as e:
            logger.exception("Agent crash after approval")
            conv_context.record_crash()
            await context.bot.send_message(
                chat_id=chat_id,
                text="Failed to execute after approval. Notifying Maleesha."
            )
            await notify_maleesha(
                context.bot,
                f"Approval execute failed\nChat: {chat_id}\nError: {str(e)[:300]}"
            )

    elif data.startswith("cancel:"):
        await query.edit_message_text(
            query.message.text + f"\n\n<b>Cancelled by {user.first_name}</b>",
            parse_mode="HTML",
        )
        clear_context(chat_id)
