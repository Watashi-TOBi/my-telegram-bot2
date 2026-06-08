import re
from datetime import timedelta, datetime, timezone
from telegram import Chat
from telegram.constants import ChatMemberStatus


def parse_duration(text: str) -> timedelta | None:
    """Parse strings like 30s, 10m, 2h, 1d into a timedelta."""
    match = re.fullmatch(r"(\d+)(s|m|h|d)", text.strip().lower())
    if not match:
        return None
    value, unit = int(match.group(1)), match.group(2)
    return timedelta(seconds=value * {"s": 1, "m": 60, "h": 3600, "d": 86400}[unit])


def until_text(td: timedelta) -> str:
    until = datetime.now(timezone.utc) + td
    return until.strftime("%Y-%m-%d %H:%M UTC")


async def is_admin(chat: Chat, user_id: int) -> bool:
    member = await chat.get_member(user_id)
    return member.status in (ChatMemberStatus.ADMINISTRATOR, ChatMemberStatus.OWNER)


async def get_target(update, context):
    """Return (user, reason) from a reply or mention, or (None, None) with error reply."""
    message = update.message
    if not message.reply_to_message:
        await message.reply_text("↩️ Reply to a user's message to use this command.")
        return None, None
    target = message.reply_to_message.from_user
    if target.is_bot:
        await message.reply_text("🤖 Can't do that to a bot.")
        return None, None
    reason = " ".join(context.args) if context.args else None
    return target, reason


async def check_can_act(update, context) -> bool:
    """Ensure caller is admin and bot is admin. Reply with error if not."""
    chat = update.effective_chat
    from telegram.constants import ChatType
    if chat.type == ChatType.PRIVATE:
        await update.message.reply_text("⚠️ Group-only command.")
        return False
    if not await is_admin(chat, update.effective_user.id):
        await update.message.reply_text("⛔ Admins only.")
        return False
    bot_member = await chat.get_member(context.bot.id)
    if bot_member.status != ChatMemberStatus.ADMINISTRATOR:
        await update.message.reply_text("⚠️ I need to be an admin first.")
        return False
    return True
