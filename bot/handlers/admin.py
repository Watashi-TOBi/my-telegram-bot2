from telegram import Update, ChatPermissions
from telegram.ext import ContextTypes
from telegram.constants import ChatType, ChatMemberStatus


async def _get_admin_and_target(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """
    Validates the command context. Returns (caller_member, target_user) on success,
    or (None, None) after sending an error reply.
    """
    chat = update.effective_chat
    message = update.message

    if chat.type == ChatType.PRIVATE:
        await message.reply_text("⚠️ This command can only be used in groups.")
        return None, None

    if not message.reply_to_message:
        await message.reply_text("↩️ Reply to a user's message to use this command.")
        return None, None

    caller = await chat.get_member(update.effective_user.id)
    if caller.status not in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER):
        await message.reply_text("⛔ You don't have permission to use this command.")
        return None, None

    target = message.reply_to_message.from_user
    if target.is_bot:
        await message.reply_text("🤖 I can't perform this action on a bot.")
        return None, None

    bot_member = await chat.get_member(context.bot.id)
    if bot_member.status != ChatMemberStatus.ADMINISTRATOR:
        await message.reply_text("⚠️ I need to be an admin to do that.")
        return None, None

    return caller, target


async def ban_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    caller, target = await _get_admin_and_target(update, context)
    if target is None:
        return

    await update.effective_chat.ban_member(target.id)
    await update.message.reply_text(
        f"🔨 <b>{target.full_name}</b> has been <b>banned</b> from the group.",
        parse_mode="HTML",
    )


async def kick_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    caller, target = await _get_admin_and_target(update, context)
    if target is None:
        return

    chat = update.effective_chat
    await chat.ban_member(target.id)
    await chat.unban_member(target.id)
    await update.message.reply_text(
        f"👢 <b>{target.full_name}</b> has been <b>kicked</b> from the group.",
        parse_mode="HTML",
    )
