from telegram import Update
from telegram.ext import ContextTypes

from utils.helpers import get_target, check_can_act
import utils.storage as storage

MAX_WARNS = 3


def _warn_key(user_id: int) -> str:
    return f"warns_{user_id}"


async def warn_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await check_can_act(update, context):
        return
    target, reason = await get_target(update, context)
    if not target:
        return

    chat = update.effective_chat
    key = _warn_key(target.id)
    data = storage.load(chat.id)
    warns = data.get(key, 0) + 1
    data[key] = warns
    storage.save(chat.id, data)

    if warns >= MAX_WARNS:
        data[key] = 0
        storage.save(chat.id, data)
        await chat.ban_member(target.id)
        await update.message.reply_text(
            f"⛔ <b>{target.full_name}</b> reached {MAX_WARNS} warnings and has been <b>banned</b>.",
            parse_mode="HTML",
        )
        return

    text = (
        f"⚠️ <b>{target.full_name}</b> has been warned. "
        f"(<b>{warns}/{MAX_WARNS}</b>)"
    )
    if reason:
        text += f"\n📝 Reason: {reason}"
    await update.message.reply_text(text, parse_mode="HTML")


async def unwarn_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await check_can_act(update, context):
        return
    target, _ = await get_target(update, context)
    if not target:
        return

    chat = update.effective_chat
    key = _warn_key(target.id)
    data = storage.load(chat.id)
    warns = max(data.get(key, 0) - 1, 0)
    data[key] = warns
    storage.save(chat.id, data)

    await update.message.reply_text(
        f"✅ Removed one warning from <b>{target.full_name}</b>. Now at <b>{warns}/{MAX_WARNS}</b>.",
        parse_mode="HTML",
    )


async def warns_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    target, _ = await get_target(update, context)
    if not target:
        return

    chat = update.effective_chat
    warns = storage.get(chat.id, _warn_key(target.id), 0)
    await update.message.reply_text(
        f"📋 <b>{target.full_name}</b> has <b>{warns}/{MAX_WARNS}</b> warnings.",
        parse_mode="HTML",
    )


async def resetwarns_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await check_can_act(update, context):
        return
    target, _ = await get_target(update, context)
    if not target:
        return

    chat = update.effective_chat
    storage.set_key(chat.id, _warn_key(target.id), 0)
    await update.message.reply_text(
        f"🔄 Warnings for <b>{target.full_name}</b> have been reset.",
        parse_mode="HTML",
    )
