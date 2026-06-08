from telegram import Update
from telegram.ext import ContextTypes

from utils.helpers import check_can_act


async def pin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await check_can_act(update, context):
        return
    if not update.message.reply_to_message:
        await update.message.reply_text("↩️ Reply to a message to pin it.")
        return

    silent = "silent" in (context.args or [])
    await update.effective_chat.pin_message(
        update.message.reply_to_message.message_id,
        disable_notification=silent,
    )
    await update.message.reply_text("📌 Message pinned.")


async def unpin_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await check_can_act(update, context):
        return

    if update.message.reply_to_message:
        await update.effective_chat.unpin_message(
            update.message.reply_to_message.message_id
        )
    else:
        await update.effective_chat.unpin_message()

    await update.message.reply_text("📌 Message unpinned.")


async def unpinall_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await check_can_act(update, context):
        return
    await update.effective_chat.unpin_all_messages()
    await update.message.reply_text("📌 All pinned messages cleared.")
