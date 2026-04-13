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

    # Security: only respond to approved chat IDs
    if chat_id not in Config.ALLOWED_CHAT_IDS:
        return

    # Strip bot mention if present (group messages often start with @MoraTechBot)
    bot_username = (await context.bot.get_me()).username
    if text.startswith(f"@{bot_username}"):
        text = text[len(f"@{bot_username}"):].strip()

    if not text:
        return

    sender = user.first_name or user.username or str(user.id)
    logger.info(f"Message from {sender} in {chat_id}: {text[:80]}")

    await context.bot.send_chat_action(chat_id=chat_id, action="typing")

    conv_context = get_context(chat_id)

    try:
        response = await run_agent_loop(text, conv_context)
        await update.message.reply_text(response, parse_mode="HTML")

    except RequiresApprovalError as e:
        # Bot tried a Tier 2 action — send approval buttons
        keyboard = [
            [
                InlineKeyboardButton("Approve", callback_data=e.approve_key()),
                InlineKeyboardButton("Cancel", callback_data=e.cancel_key()),
            ]
        ]
        await update.message.reply_text(
            e.approval_message(),
            reply_markup=InlineKeyboardMarkup(keyboard),
            parse_mode="HTML",
        )

    except Exception as e:
        logger.exception(f"Agent crash handling: {text}")
        await update.message.reply_text(
            "Something went wrong on my end. Notifying Maleesha."
        )
        await notify_maleesha(
            context.bot,
            f"Tech bot crashed\n\nChat: {chat_id}\nMessage: {text}\nError: {e}",
        )


async def handle_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    chat_id = query.message.chat_id
    user = query.from_user
    data = query.data or ""

    # Security check
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
            await context.bot.send_message(chat_id=chat_id, text="Failed to execute after approval. Notifying Maleesha.")
            await notify_maleesha(context.bot, f"Approval execute failed\nChat: {chat_id}\nError: {e}")

    elif data.startswith("cancel:"):
        await query.edit_message_text(
            query.message.text + f"\n\n<b>Cancelled by {user.first_name}</b>",
            parse_mode="HTML",
        )
        clear_context(chat_id)
