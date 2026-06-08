import os
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

from config import SUPPORT_URL, OWNER_URL, SOURCE_URL

_ASSETS_DIR = os.path.join(os.path.dirname(__file__), "..", "assets")
_BANNER = os.path.join(_ASSETS_DIR, "start_banner.jpg")


def _build_keyboard(bot_username: str) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(
            "📤 ADD ME TO YOUR GROUP",
            url=f"https://t.me/{bot_username}?startgroup=true",
        )],
        [
            InlineKeyboardButton("💫 Support", url=SUPPORT_URL),
            InlineKeyboardButton("▶️ Owner",   url=OWNER_URL),
        ],
        [
            InlineKeyboardButton("❓ Help", callback_data="show_help"),
            InlineKeyboardButton("🔗 Join", url="https://t.me/Graveyard_of_S0UL"),
        ],
    ])


async def start_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    bot  = context.bot

    caption = (
        f"👋 Hey, <b>{user.first_name}</b> 🐻\n\n"
        f"<i>\"Your group's guardian\"</i>\n\n"
        f"🖤 I am <b>{bot.first_name}</b>, your versatile management bot, "
        f"designed to help you take control of your groups with ease "
        f"using my powerful modules and commands!\n\n"
        f"💎 <b>What I Can Do:</b>\n\n"
        f"• 🛡️  Seamless management of your groups\n"
        f"• 🔧  Powerful moderation tools\n"
        f"• ✨  Fun and engaging features\n\n"
        f"⭐ <b>Need Help?</b>\n"
        f"Click the help button below."
    )

    keyboard = _build_keyboard(bot.username)

    with open(_BANNER, "rb") as photo:
        await update.message.reply_photo(
            photo=photo,
            caption=caption,
            parse_mode="HTML",
            reply_markup=keyboard,
        )


async def commands_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    commands_text = (
        "📋 <b>Quick Command Reference</b>\n\n"
        "🎭 <b>Mafia Game</b>\n"
        "• /startgame /join /flee /startmafia\n"
        "• /players /skip /endgame /stats /gamerules\n\n"
        "⚙️ <b>Moderation</b>\n"
        "• /ban /kick /tban /mute /unmute /tmute\n"
        "• /warn /unwarn /warns /resetwarns\n"
        "• /promote /demote /purge /pin /unpin\n"
        "• /lock /unlock /locks\n\n"
        "💬 <b>Group Tools</b>\n"
        "• /filter /filters /stop — keyword auto-replies\n"
        "• /setrules /rules — group rules\n"
        "• /report — alert admins\n\n"
        "🎉 <b>Fun</b>\n"
        "• /love /crush /q /kang\n"
        "• /hug /kiss /slap /pat /cuddle\n"
        "• /poke /bite /punch /wink /baka\n\n"
        "🤖 <b>AI Chat</b>\n"
        "• DM me · @mention me · reply to my message\n\n"
        "📖 Use /help for the full detailed guide!"
    )

    await query.edit_message_caption(
        caption=commands_text,
        parse_mode="HTML",
        reply_markup=InlineKeyboardMarkup([
            [InlineKeyboardButton("🔙 Back", callback_data="show_start")],
        ]),
    )


async def back_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()

    # If this is a plain text message (e.g. the help reply), just delete it.
    # The original /start photo is still visible above it in the chat.
    if not query.message.photo:
        await query.message.delete()
        return

    user = query.from_user
    bot  = context.bot

    caption = (
        f"👋 Hey, <b>{user.first_name}</b> 🐻\n\n"
        f"<i>\"Your group's guardian\"</i>\n\n"
        f"🖤 I am <b>{bot.first_name}</b>, your versatile management bot, "
        f"designed to help you take control of your groups with ease "
        f"using my powerful modules and commands!\n\n"
        f"💎 <b>What I Can Do:</b>\n\n"
        f"• 🛡️  Seamless management of your groups\n"
        f"• 🔧  Powerful moderation tools\n"
        f"• ✨  Fun and engaging features\n\n"
        f"⭐ <b>Need Help?</b>\n"
        f"Click the help button below."
    )

    await query.edit_message_caption(
        caption=caption,
        parse_mode="HTML",
        reply_markup=_build_keyboard(bot.username),
    )
