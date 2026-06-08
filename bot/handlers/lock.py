from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes
from telegram.constants import ChatType

from utils.helpers import check_can_act
import utils.storage as storage

LOCK_TYPES = {
    "text":     "can_send_messages",
    "media":    "can_send_photos",
    "sticker":  "can_send_other_messages",
    "gif":      "can_send_other_messages",
    "poll":     "can_send_polls",
    "forward":  None,
    "link":     "can_add_web_page_previews",
}

_HELP = "Available lock types: " + ", ".join(f"<code>{k}</code>" for k in LOCK_TYPES)


def _build_permissions(locked: dict) -> ChatPermissions:
    return ChatPermissions(
        can_send_messages       = not locked.get("text", False),
        can_send_audios         = not locked.get("media", False),
        can_send_documents      = not locked.get("media", False),
        can_send_photos         = not locked.get("media", False),
        can_send_videos         = not locked.get("media", False),
        can_send_video_notes    = not locked.get("media", False),
        can_send_voice_notes    = not locked.get("media", False),
        can_send_polls          = not locked.get("poll", False),
        can_send_other_messages = not (locked.get("sticker", False) or locked.get("gif", False)),
        can_add_web_page_previews = not locked.get("link", False),
    )


async def lock_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await check_can_act(update, context):
        return
    if not context.args:
        await update.message.reply_text(f"Usage: /lock [type]\n{_HELP}", parse_mode="HTML")
        return

    lock_type = context.args[0].lower()
    if lock_type not in LOCK_TYPES:
        await update.message.reply_text(f"❌ Unknown type.\n{_HELP}", parse_mode="HTML")
        return

    chat_id = update.effective_chat.id
    data = storage.load(chat_id)
    locked = data.get("locks", {})
    locked[lock_type] = True
    data["locks"] = locked
    storage.save(chat_id, data)

    await update.effective_chat.set_permissions(_build_permissions(locked))
    await update.message.reply_text(f"🔒 <b>{lock_type}</b> has been locked.", parse_mode="HTML")


async def unlock_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await check_can_act(update, context):
        return
    if not context.args:
        await update.message.reply_text(f"Usage: /unlock [type]\n{_HELP}", parse_mode="HTML")
        return

    lock_type = context.args[0].lower()
    if lock_type not in LOCK_TYPES:
        await update.message.reply_text(f"❌ Unknown type.\n{_HELP}", parse_mode="HTML")
        return

    chat_id = update.effective_chat.id
    data = storage.load(chat_id)
    locked = data.get("locks", {})
    locked.pop(lock_type, None)
    data["locks"] = locked
    storage.save(chat_id, data)

    await update.effective_chat.set_permissions(_build_permissions(locked))
    await update.message.reply_text(f"🔓 <b>{lock_type}</b> has been unlocked.", parse_mode="HTML")


async def locks_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat_id = update.effective_chat.id
    locked = storage.get(chat_id, "locks", {})

    lines = []
    for lt in LOCK_TYPES:
        icon = "🔒" if locked.get(lt) else "🔓"
        lines.append(f"{icon} {lt}")

    await update.message.reply_text(
        "🔐 <b>Lock Status</b>\n\n" + "\n".join(lines),
        parse_mode="HTML",
    )
