from datetime import datetime, timezone
from telegram import Update
from telegram.ext import ContextTypes

from utils.helpers import parse_duration, until_text, get_target, check_can_act


async def tban_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await check_can_act(update, context):
        return
    if not context.args:
        await update.message.reply_text("Usage: /tban [duration] — e.g. <code>/tban 1h</code>", parse_mode="HTML")
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
    await chat.ban_member(target.id, until_date=until)

    text = f"🔨 <b>{target.full_name}</b> banned until <b>{until_text(td)}</b>."
    if reason:
        text += f"\n📝 Reason: {reason}"
    await update.message.reply_text(text, parse_mode="HTML")
