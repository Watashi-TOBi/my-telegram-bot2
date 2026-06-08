from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatType

from utils.helpers import check_can_act
import utils.storage as storage


def _filters_key() -> str:
    return "filters"


async def filter_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Add a keyword filter: /filter keyword Reply text"""
    if not await check_can_act(update, context):
        return

    if len(context.args) < 2:
        await update.message.reply_text(
            "Usage: <code>/filter keyword reply text</code>",
            parse_mode="HTML",
        )
        return

    keyword = context.args[0].lower()
    reply_text = " ".join(context.args[1:])

    chat_id = update.effective_chat.id
    data = storage.load(chat_id)
    filters = data.get(_filters_key(), {})
    filters[keyword] = reply_text
    data[_filters_key()] = filters
    storage.save(chat_id, data)

    await update.message.reply_text(
        f"✅ Filter set for keyword: <code>{keyword}</code>",
        parse_mode="HTML",
    )


async def stop_filter_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Remove a keyword filter: /stop keyword"""
    if not await check_can_act(update, context):
        return

    if not context.args:
        await update.message.reply_text("Usage: <code>/stop keyword</code>", parse_mode="HTML")
        return

    keyword = context.args[0].lower()
    chat_id = update.effective_chat.id
    data = storage.load(chat_id)
    filters = data.get(_filters_key(), {})

    if keyword not in filters:
        await update.message.reply_text(f"❌ No filter found for: <code>{keyword}</code>", parse_mode="HTML")
        return

    del filters[keyword]
    data[_filters_key()] = filters
    storage.save(chat_id, data)

    await update.message.reply_text(f"🗑️ Filter removed for: <code>{keyword}</code>", parse_mode="HTML")


async def list_filters_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """List all active filters: /filters"""
    chat_id = update.effective_chat.id
    filters = storage.get(chat_id, _filters_key(), {})

    if not filters:
        await update.message.reply_text("📋 No active filters in this group.")
        return

    lines = "\n".join(f"• <code>{k}</code>" for k in filters)
    await update.message.reply_text(
        f"📋 <b>Active Filters</b>\n\n{lines}",
        parse_mode="HTML",
    )


async def check_filters(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Auto-reply when a message matches a keyword filter."""
    chat = update.effective_chat
    message = update.message
    if not message or not message.text:
        return

    text = message.text.lower()
    filters = storage.get(chat.id, _filters_key(), {})

    for keyword, reply_text in filters.items():
        if keyword in text:
            await message.reply_text(reply_text)
            break
