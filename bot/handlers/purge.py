from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatType

from utils.helpers import is_admin


async def purge_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    message = update.message

    if chat.type == ChatType.PRIVATE:
        await message.reply_text("⚠️ Group-only command.")
        return
    if not await is_admin(chat, update.effective_user.id):
        await message.reply_text("⛔ Admins only.")
        return
    if not message.reply_to_message:
        await message.reply_text("↩️ Reply to the first message you want to delete.")
        return

    from_id = message.reply_to_message.message_id
    to_id   = message.message_id

    ids_to_delete = list(range(from_id, to_id + 1))

    deleted = 0
    for chunk_start in range(0, len(ids_to_delete), 100):
        chunk = ids_to_delete[chunk_start:chunk_start + 100]
        try:
            await context.bot.delete_messages(chat.id, chunk)
            deleted += len(chunk)
        except Exception:
            for mid in chunk:
                try:
                    await context.bot.delete_message(chat.id, mid)
                    deleted += 1
                except Exception:
                    pass

    note = await context.bot.send_message(
        chat.id,
        f"🗑️ Purged <b>{deleted}</b> messages.",
        parse_mode="HTML",
    )
    import asyncio
    await asyncio.sleep(4)
    try:
        await note.delete()
    except Exception:
        pass
