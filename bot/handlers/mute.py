import asyncio
from datetime import datetime, timezone
from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes

from utils.helpers import parse_duration, until_text, get_target, check_can_act

_MUTED = ChatPermissions(
    can_send_messages=False,
    can_send_audios=False,
    can_send_documents=False,
    can_send_photos=False,
    can_send_videos=False,
    can_send_video_notes=False,
    can_send_voice_notes=False,
    can_send_polls=False,
    can_send_other_messages=False,
    can_add_web_page_previews=False,
)
_FREE = ChatPermissions(
    can_send_messages=True,
    can_send_audios=True,
    can_send_documents=True,
    can_send_photos=True,
    can_send_videos=True,
    can_send_video_notes=True,
    can_send_voice_notes=True,
    can_send_polls=True,
    can_send_other_messages=True,
    can_add_web_page_previews=True,
)


async def mute_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await check_can_act(update, context):
        return
    target, reason = await get_target(update, context)
    if not target:
        return

    await update.effective_chat.restrict_member(target.id, _MUTED)
    text = f"🔇 <b>{target.full_name}</b> has been muted."
    if reason:
        text += f"\n📝 Reason: {reason}"
    await update.message.reply_text(text, parse_mode="HTML")


async def unmute_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await check_can_act(update, context):
        return
    target, _ = await get_target(update, context)
    if not target:
        return

    await update.effective_chat.restrict_member(target.id, _FREE)
    await update.message.reply_text(
        f"🔊 <b>{target.full_name}</b> has been unmuted.",
        parse_mode="HTML",
    )


async def tmute_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await check_can_act(update, context):
        return
    if not context.args:
        await update.message.reply_text("Usage: /tmute [duration] — e.g. <code>/tmute 30m</code>", parse_mode="HTML")
        return

    td = parse_duration(context.args[0])
    if not td:
        await update.message.reply_text("⚠️ Invalid duration. Use: 30s, 10m, 2h, 1d")
        return

    target, reason = await get_target(update, context)
    if not target:
        return

    chat = update.effective_chat
    until = datetime.now(timezone.utc) + td
    await chat.restrict_member(target.id, _MUTED, until_date=until)

    text = f"🔇 <b>{target.full_name}</b> muted until <b>{until_text(td)}</b>."
    if reason:
        text += f"\n📝 Reason: {reason}"
    await update.message.reply_text(text, parse_mode="HTML")
