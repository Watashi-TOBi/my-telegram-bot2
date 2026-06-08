from telegram import Update, ChatMemberUpdated
from telegram.ext import ContextTypes
from telegram.constants import ChatMemberStatus


def _status_change(member_update: ChatMemberUpdated):
    """Returns ('joined' | 'left' | None) based on old vs new membership status."""
    old_status = member_update.old_chat_member.status
    new_status = member_update.new_chat_member.status

    was_member = old_status in (
        ChatMemberStatus.MEMBER,
        ChatMemberStatus.ADMINISTRATOR,
        ChatMemberStatus.OWNER,
        ChatMemberStatus.RESTRICTED,
    )
    is_member = new_status in (
        ChatMemberStatus.MEMBER,
        ChatMemberStatus.ADMINISTRATOR,
        ChatMemberStatus.OWNER,
        ChatMemberStatus.RESTRICTED,
    )

    if not was_member and is_member:
        return "joined"
    if was_member and not is_member:
        return "left"
    return None


async def member_update_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    # Handle new_chat_members status update messages
    if update.message:
        msg = update.message
        if msg.new_chat_members:
            for user in msg.new_chat_members:
                if user.id == context.bot.id:
                    continue
                await msg.reply_text(
                    f"👋 Welcome to the group, <b>{user.full_name}</b>! "
                    f"We're glad to have you here. 🎉",
                    parse_mode="HTML",
                )
        elif msg.left_chat_member:
            user = msg.left_chat_member
            if user.id != context.bot.id:
                await msg.reply_text(
                    f"😢 <b>{user.full_name}</b> has left the group. Goodbye!",
                    parse_mode="HTML",
                )
        return

    # Handle ChatMember updates (for bots with admin rights)
    if not update.chat_member:
        return

    change = _status_change(update.chat_member)
    user = update.chat_member.new_chat_member.user
    chat = update.effective_chat

    if change == "joined":
        await context.bot.send_message(
            chat_id=chat.id,
            text=(
                f"👋 Welcome to <b>{chat.title}</b>, <b>{user.full_name}</b>! "
                f"We're glad to have you here. 🎉"
            ),
            parse_mode="HTML",
        )
    elif change == "left":
        await context.bot.send_message(
            chat_id=chat.id,
            text=f"😢 <b>{user.full_name}</b> has left the group. Goodbye!",
            parse_mode="HTML",
        )
