from telegram import Update
from telegram.ext import ContextTypes

from utils.helpers import check_can_act, get_target


async def promote_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await check_can_act(update, context):
        return
    target, _ = await get_target(update, context)
    if not target:
        return

    await update.effective_chat.promote_member(
        target.id,
        can_manage_chat=True,
        can_delete_messages=True,
        can_manage_video_chats=True,
        can_restrict_members=True,
        can_promote_members=False,
        can_change_info=True,
        can_invite_users=True,
        can_pin_messages=True,
        can_post_stories=False,
        can_edit_stories=False,
        can_delete_stories=False,
        is_anonymous=False,
    )
    await update.message.reply_text(
        f"⭐ <b>{target.full_name}</b> has been promoted to admin.",
        parse_mode="HTML",
    )


async def demote_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await check_can_act(update, context):
        return
    target, _ = await get_target(update, context)
    if not target:
        return

    await update.effective_chat.promote_member(
        target.id,
        can_manage_chat=False,
        can_delete_messages=False,
        can_manage_video_chats=False,
        can_restrict_members=False,
        can_promote_members=False,
        can_change_info=False,
        can_invite_users=False,
        can_pin_messages=False,
        can_post_stories=False,
        can_edit_stories=False,
        can_delete_stories=False,
        is_anonymous=False,
    )
    await update.message.reply_text(
        f"🔽 <b>{target.full_name}</b> has been demoted.",
        parse_mode="HTML",
    )
