from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatType, ChatMemberStatus


async def report_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    message = update.message

    if chat.type == ChatType.PRIVATE:
        await message.reply_text("⚠️ This command is for groups only.")
        return
    if not message.reply_to_message:
        await message.reply_text("↩️ Reply to the message you want to report.")
        return

    reported_user = message.reply_to_message.from_user
    reporter = update.effective_user
    reason = " ".join(context.args) if context.args else "No reason given"

    admins = await chat.get_administrators()
    mentions = " ".join(
        f'<a href="tg://user?id={a.user.id}">.</a>'
        for a in admins
        if not a.user.is_bot
    )

    await message.reply_text(
        f"🚨 <b>Report</b>\n\n"
        f"👤 Reported: <b>{reported_user.full_name}</b>\n"
        f"📝 Reason: {reason}\n\n"
        f"Admins notified: {mentions}",
        parse_mode="HTML",
    )
