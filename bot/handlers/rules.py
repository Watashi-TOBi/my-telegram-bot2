from telegram import Update
from telegram.ext import ContextTypes

from utils.helpers import check_can_act
import utils.storage as storage


async def setrules_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not await check_can_act(update, context):
        return

    if not context.args:
        await update.message.reply_text(
            "Usage: <code>/setrules Your rules here...</code>",
            parse_mode="HTML",
        )
        return

    rules_text = " ".join(context.args)
    storage.set_key(update.effective_chat.id, "rules", rules_text)
    await update.message.reply_text("✅ Group rules have been updated.")


async def rules_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    rules = storage.get(update.effective_chat.id, "rules")
    if not rules:
        await update.message.reply_text("📋 No rules have been set for this group yet.")
        return
    await update.message.reply_text(
        f"📋 <b>Group Rules</b>\n\n{rules}",
        parse_mode="HTML",
    )
