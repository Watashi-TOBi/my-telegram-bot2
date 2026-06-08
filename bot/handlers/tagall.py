import logging
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatType
from telegram.error import BadRequest
from utils.members import get_members

logger = logging.getLogger(__name__)

MAX_MENTIONS_PER_MSG = 20  # stay well under Telegram's entity limit


async def _do_tagall(update: Update, context: ContextTypes.DEFAULT_TYPE, reason: str = "") -> None:
    chat = update.effective_chat
    msg  = update.message

    if chat.type == ChatType.PRIVATE:
        await msg.reply_text("Use this in a group!")
        return

    # Admins only — prevents spam abuse
    member = await chat.get_member(update.effective_user.id)
    if member.status not in ("administrator", "creator"):
        await msg.reply_text("⛔ Only admins can tag everyone.")
        return

    members = get_members(chat.id)
    if not members:
        await msg.reply_text("No members tracked yet. Members are recorded as they chat.")
        return

    header = f"📢 <b>Attention everyone!</b>"
    if reason:
        header += f"\n{reason}"
    header += "\n\n"

    # Build batches of MAX_MENTIONS_PER_MSG
    items    = list(members.items())
    batches  = [items[i:i + MAX_MENTIONS_PER_MSG] for i in range(0, len(items), MAX_MENTIONS_PER_MSG)]

    for idx, batch in enumerate(batches):
        mentions = " ".join(
            f'<a href="tg://user?id={uid}">{name}</a>'
            for uid, name in batch
        )
        text = (header if idx == 0 else "") + mentions
        try:
            await context.bot.send_message(
                chat_id=chat.id,
                text=text,
                parse_mode="HTML",
            )
        except BadRequest as e:
            logger.warning("tagall batch error: %s", e)


async def tagall_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    reason = " ".join(context.args) if context.args else ""
    await _do_tagall(update, context, reason)


async def tagall_message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Fires when someone types @all in a group message."""
    msg  = update.message
    if not msg or not msg.text:
        return

    if "@all" not in msg.text.lower():
        return

    chat = update.effective_chat
    if chat.type == ChatType.PRIVATE:
        return

    # Extract any text after @all as the reason
    text   = msg.text
    idx    = text.lower().find("@all")
    reason = text[idx + 4:].strip()

    await _do_tagall(update, context, reason)
