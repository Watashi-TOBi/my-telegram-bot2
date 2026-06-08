import logging
from telegram import Update, BotCommand, BotCommandScopeAllGroupChats, BotCommandScopeAllPrivateChats
from telegram.ext import (
    ApplicationBuilder,
    CommandHandler,
    ContextTypes,
    MessageHandler,
    ChatMemberHandler,
    CallbackQueryHandler,
    filters,
)

from config import TELEGRAM_TOKEN

from handlers.start          import start_handler, commands_callback, back_callback
from handlers.help           import help_handler, help_callback
from handlers.admin          import ban_handler, kick_handler
from handlers.mute           import mute_handler, unmute_handler, tmute_handler
from handlers.tban           import tban_handler
from handlers.warn           import warn_handler, unwarn_handler, warns_handler, resetwarns_handler
from handlers.purge          import purge_handler
from handlers.pin            import pin_handler, unpin_handler, unpinall_handler
from handlers.promote        import promote_handler, demote_handler
from handlers.rules          import rules_handler, setrules_handler
from handlers.report         import report_handler
from handlers.filter_handler import (
    filter_handler, stop_filter_handler, list_filters_handler, check_filters,
)
from handlers.lock           import lock_handler, unlock_handler, locks_handler
from handlers.welcome        import member_update_handler
from utils.members           import track as track_member
from handlers.fun            import love_handler, crush_handler
from handlers.quote_sticker  import quote_handler, kang_handler
from handlers.ai_chat        import ai_chat_handler
from handlers.mafia          import (
    startgame_handler, join_handler, flee_handler, startmafia_handler,
    resend_handler, players_handler, endgame_handler, skip_handler,
    gamerules_handler, mafia_callback,
)
from handlers.stats          import stats_handler
from handlers.economy        import (
    bal_handler, daily_handler, weekly_handler, monthly_handler,
    kill_handler, rob_handler, leaderboard_handler, topkills_handler,
    lb_callback,
)
from handlers.shop           import shop_handler, shop_callback
from handlers.duel           import duel_handler, duel_callback
from handlers.games          import (
    bet_handler, football_handler, basket_handler,
    bowling_handler, dart_handler, slot_handler,
)
from handlers.truth_dare     import truth_handler, dare_handler
from handlers.tagall         import tagall_handler, tagall_message_handler
from handlers.anime          import (
    hug_handler, kiss_handler, slap_handler, pat_handler,
    cuddle_handler, poke_handler, bite_handler, punch_handler,
    wink_handler, baka_handler,
)

logging.basicConfig(
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    level=logging.INFO,
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)

_PRIVATE_COMMANDS = [
    BotCommand("start",       "Show the welcome message"),
    BotCommand("help",        "Full command guide"),
    BotCommand("bal",         "Check your coin balance"),
    BotCommand("daily",       "Claim 1,000 free coins (24h)"),
    BotCommand("weekly",      "Claim 5,000 free coins (7 days)"),
    BotCommand("monthly",     "Claim 20,000 free coins (30 days)"),
    BotCommand("shop",        "Buy weapons, food & titles"),
    BotCommand("duel",        "Duel someone for coins (reply)"),
    BotCommand("bet",         "Bet coins on a dice roll"),
    BotCommand("slot",        "Spin the slot machine"),
    BotCommand("truth",       "Get a random truth question"),
    BotCommand("dare",        "Get a random dare challenge"),
    BotCommand("love",        "Love compatibility calculator"),
    BotCommand("q",           "Fancy quote sticker (reply)"),
    BotCommand("kang",        "Steal a sticker into your pack (reply)"),
    BotCommand("hug",         "Hug someone (reply)"),
    BotCommand("kiss",        "Kiss someone (reply)"),
    BotCommand("slap",        "Slap someone (reply)"),
    BotCommand("pat",         "Pat someone (reply)"),
    BotCommand("cuddle",      "Cuddle someone (reply)"),
    BotCommand("poke",        "Poke someone (reply)"),
    BotCommand("bite",        "Bite someone (reply)"),
    BotCommand("punch",       "Punch someone (reply)"),
    BotCommand("wink",        "Wink at someone (reply)"),
    BotCommand("baka",        "Call someone a baka! (reply)"),
]

_GROUP_COMMANDS = [
    BotCommand("start",       "Welcome message"),
    BotCommand("help",        "Full command guide"),
    # Economy
    BotCommand("bal",         "Check coin balance"),
    BotCommand("daily",       "Claim 1,000 free coins (24h)"),
    BotCommand("weekly",      "Claim 5,000 free coins (7 days)"),
    BotCommand("monthly",     "Claim 20,000 free coins (30 days)"),
    BotCommand("kill",        "Kill someone for coins (reply)"),
    BotCommand("rob",         "Rob someone's coins (reply)"),
    BotCommand("leaderboard", "Richest members — group & global"),
    BotCommand("topkills",    "Top killers — group & global"),
    BotCommand("shop",        "Buy weapons, food & titles"),
    BotCommand("duel",        "Challenge someone to a duel (reply)"),
    # Games
    BotCommand("bet",         "Bet coins — /bet 100"),
    BotCommand("football",    "Play football for coins ⚽"),
    BotCommand("basket",      "Play basketball for coins 🏀"),
    BotCommand("bowling",     "Play bowling for coins 🎳"),
    BotCommand("dart",        "Throw a dart for coins 🎯"),
    BotCommand("slot",        "Spin the slot machine 🎰"),
    # Truth or dare
    BotCommand("truth",       "Get a truth question"),
    BotCommand("dare",        "Get a dare challenge"),
    # Tag
    BotCommand("tagall",      "Tag all members (admins only)"),
    # Mafia
    BotCommand("startgame",   "Start a Mafia game lobby"),
    BotCommand("join",        "Join the Mafia lobby"),
    BotCommand("flee",        "Leave the Mafia lobby"),
    BotCommand("startmafia",  "Begin the Mafia game (host)"),
    BotCommand("resend",      "Resend your Mafia role to DM"),
    BotCommand("players",     "Show alive/dead players"),
    BotCommand("stats",       "Your Mafia win/loss record"),
    BotCommand("skip",        "Skip current phase (host/admin)"),
    BotCommand("endgame",     "Cancel the game (host/admin)"),
    BotCommand("gamerules",   "How to play Mafia"),
    # Fun
    BotCommand("love",        "Love compatibility — /love Name1 Name2"),
    BotCommand("crush",       "Reveal someone's secret crush (reply)"),
    BotCommand("q",           "Fancy quote sticker (reply)"),
    BotCommand("kang",        "Steal a sticker into your pack (reply)"),
    BotCommand("hug",         "Hug someone (reply)"),
    BotCommand("kiss",        "Kiss someone (reply)"),
    BotCommand("slap",        "Slap someone (reply)"),
    BotCommand("pat",         "Pat someone (reply)"),
    BotCommand("cuddle",      "Cuddle someone (reply)"),
    BotCommand("poke",        "Poke someone (reply)"),
    BotCommand("bite",        "Bite someone (reply)"),
    BotCommand("punch",       "Punch someone (reply)"),
    BotCommand("wink",        "Wink at someone (reply)"),
    BotCommand("baka",        "Call someone a baka! (reply)"),
    # Moderation
    BotCommand("ban",         "Ban a user (reply)"),
    BotCommand("kick",        "Kick a user (reply)"),
    BotCommand("tban",        "Temp-ban — /tban 1h (reply)"),
    BotCommand("mute",        "Mute a user (reply)"),
    BotCommand("unmute",      "Unmute a user (reply)"),
    BotCommand("tmute",       "Temp-mute — /tmute 30m (reply)"),
    BotCommand("warn",        "Warn a user (reply)"),
    BotCommand("unwarn",      "Remove a warning (reply)"),
    BotCommand("warns",       "Check warnings (reply)"),
    BotCommand("resetwarns",  "Clear all warnings (reply)"),
    BotCommand("purge",       "Delete messages from reply to here"),
    BotCommand("pin",         "Pin a message (reply)"),
    BotCommand("unpin",       "Unpin a message"),
    BotCommand("unpinall",    "Unpin all messages"),
    BotCommand("promote",     "Promote to admin (reply)"),
    BotCommand("demote",      "Remove admin rights (reply)"),
    BotCommand("lock",        "Lock content type — /lock media"),
    BotCommand("unlock",      "Unlock content type"),
    BotCommand("locks",       "Show lock status"),
    BotCommand("filter",      "Add keyword filter — /filter hi Hello!"),
    BotCommand("filters",     "List active filters"),
    BotCommand("stop",        "Remove a filter"),
    BotCommand("rules",       "Show group rules"),
    BotCommand("setrules",    "Set group rules"),
    BotCommand("report",      "Report a user to admins (reply)"),
]


async def _set_commands(app) -> None:
    await app.bot.set_my_commands(_PRIVATE_COMMANDS, scope=BotCommandScopeAllPrivateChats())
    await app.bot.set_my_commands(_GROUP_COMMANDS,   scope=BotCommandScopeAllGroupChats())
    logger.info("Bot commands registered.")


def main() -> None:
    app = ApplicationBuilder().token(TELEGRAM_TOKEN).post_init(_set_commands).build()

    # ── General ────────────────────────────────────────────────────────────────
    app.add_handler(CommandHandler("start", start_handler))
    app.add_handler(CommandHandler("help",  help_handler))

    # ── Economy ────────────────────────────────────────────────────────────────
    app.add_handler(CommandHandler("bal",         bal_handler))
    app.add_handler(CommandHandler("daily",       daily_handler))
    app.add_handler(CommandHandler("weekly",      weekly_handler))
    app.add_handler(CommandHandler("monthly",     monthly_handler))
    app.add_handler(CommandHandler("kill",        kill_handler))
    app.add_handler(CommandHandler("rob",         rob_handler))
    app.add_handler(CommandHandler("leaderboard", leaderboard_handler))
    app.add_handler(CommandHandler("topkills",    topkills_handler))

    # ── Shop & Duel ────────────────────────────────────────────────────────────
    app.add_handler(CommandHandler("shop",  shop_handler))
    app.add_handler(CommandHandler("duel",  duel_handler))

    # ── Games ──────────────────────────────────────────────────────────────────
    app.add_handler(CommandHandler("bet",      bet_handler))
    app.add_handler(CommandHandler("football", football_handler))
    app.add_handler(CommandHandler("basket",   basket_handler))
    app.add_handler(CommandHandler("bowling",  bowling_handler))
    app.add_handler(CommandHandler("dart",     dart_handler))
    app.add_handler(CommandHandler("slot",     slot_handler))

    # ── Truth or Dare ──────────────────────────────────────────────────────────
    app.add_handler(CommandHandler("truth", truth_handler))
    app.add_handler(CommandHandler("dare",  dare_handler))

    # ── Tag all ────────────────────────────────────────────────────────────────
    app.add_handler(CommandHandler("tagall", tagall_handler))

    # ── Fun ────────────────────────────────────────────────────────────────────
    app.add_handler(CommandHandler("love",  love_handler))
    app.add_handler(CommandHandler("crush", crush_handler))
    app.add_handler(CommandHandler("q",     quote_handler))
    app.add_handler(CommandHandler("kang",  kang_handler))

    # ── Anime / fun interaction ────────────────────────────────────────────────
    app.add_handler(CommandHandler("hug",    hug_handler))
    app.add_handler(CommandHandler("kiss",   kiss_handler))
    app.add_handler(CommandHandler("slap",   slap_handler))
    app.add_handler(CommandHandler("pat",    pat_handler))
    app.add_handler(CommandHandler("cuddle", cuddle_handler))
    app.add_handler(CommandHandler("poke",   poke_handler))
    app.add_handler(CommandHandler("bite",   bite_handler))
    app.add_handler(CommandHandler("punch",  punch_handler))
    app.add_handler(CommandHandler("wink",   wink_handler))
    app.add_handler(CommandHandler("baka",   baka_handler))

    # ── Callback buttons ───────────────────────────────────────────────────────
    app.add_handler(CallbackQueryHandler(help_callback,     pattern="^show_help$"))
    app.add_handler(CallbackQueryHandler(commands_callback, pattern="^show_commands$"))
    app.add_handler(CallbackQueryHandler(back_callback,     pattern="^show_start$"))
    app.add_handler(CallbackQueryHandler(mafia_callback,    pattern="^mg_"))
    app.add_handler(CallbackQueryHandler(shop_callback,     pattern="^sh\\|"))
    app.add_handler(CallbackQueryHandler(duel_callback,     pattern="^duel\\|"))
    app.add_handler(CallbackQueryHandler(lb_callback,       pattern="^lb\\|"))

    # ── Mafia game ─────────────────────────────────────────────────────────────
    app.add_handler(CommandHandler("startgame",  startgame_handler))
    app.add_handler(CommandHandler("join",       join_handler))
    app.add_handler(CommandHandler("flee",       flee_handler))
    app.add_handler(CommandHandler("startmafia", startmafia_handler))
    app.add_handler(CommandHandler("resend",     resend_handler))
    app.add_handler(CommandHandler("players",    players_handler))
    app.add_handler(CommandHandler("stats",      stats_handler))
    app.add_handler(CommandHandler("skip",       skip_handler))
    app.add_handler(CommandHandler("endgame",    endgame_handler))
    app.add_handler(CommandHandler("gamerules",  gamerules_handler))

    # ── Admin — ban/kick ───────────────────────────────────────────────────────
    app.add_handler(CommandHandler("ban",  ban_handler))
    app.add_handler(CommandHandler("kick", kick_handler))
    app.add_handler(CommandHandler("tban", tban_handler))

    # ── Admin — mute ───────────────────────────────────────────────────────────
    app.add_handler(CommandHandler("mute",   mute_handler))
    app.add_handler(CommandHandler("unmute", unmute_handler))
    app.add_handler(CommandHandler("tmute",  tmute_handler))

    # ── Admin — warnings ───────────────────────────────────────────────────────
    app.add_handler(CommandHandler("warn",       warn_handler))
    app.add_handler(CommandHandler("unwarn",     unwarn_handler))
    app.add_handler(CommandHandler("warns",      warns_handler))
    app.add_handler(CommandHandler("resetwarns", resetwarns_handler))

    # ── Admin — messages ───────────────────────────────────────────────────────
    app.add_handler(CommandHandler("purge",    purge_handler))
    app.add_handler(CommandHandler("pin",      pin_handler))
    app.add_handler(CommandHandler("unpin",    unpin_handler))
    app.add_handler(CommandHandler("unpinall", unpinall_handler))

    # ── Admin — roles ──────────────────────────────────────────────────────────
    app.add_handler(CommandHandler("promote", promote_handler))
    app.add_handler(CommandHandler("demote",  demote_handler))

    # ── Admin — locks ──────────────────────────────────────────────────────────
    app.add_handler(CommandHandler("lock",   lock_handler))
    app.add_handler(CommandHandler("unlock", unlock_handler))
    app.add_handler(CommandHandler("locks",  locks_handler))

    # ── Group info ─────────────────────────────────────────────────────────────
    app.add_handler(CommandHandler("rules",    rules_handler))
    app.add_handler(CommandHandler("setrules", setrules_handler))
    app.add_handler(CommandHandler("report",   report_handler))

    # ── Keyword filters ────────────────────────────────────────────────────────
    app.add_handler(CommandHandler("filter",  filter_handler))
    app.add_handler(CommandHandler("filters", list_filters_handler))
    app.add_handler(CommandHandler("stop",    stop_filter_handler))

    # ── Member join/leave ──────────────────────────────────────────────────────
    app.add_handler(ChatMemberHandler(member_update_handler, ChatMemberHandler.CHAT_MEMBER))
    app.add_handler(MessageHandler(filters.StatusUpdate.NEW_CHAT_MEMBERS, member_update_handler))
    app.add_handler(MessageHandler(filters.StatusUpdate.LEFT_CHAT_MEMBER, member_update_handler))

    # ── Member tracker ─────────────────────────────────────────────────────────
    async def _track(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
        user = update.effective_user
        chat = update.effective_chat
        if user and chat and chat.type in ("group", "supergroup"):
            track_member(chat.id, user.id, user.first_name)

    app.add_handler(MessageHandler(filters.ALL & filters.ChatType.GROUPS, _track), group=0)

    # ── @all trigger ───────────────────────────────────────────────────────────
    app.add_handler(
        MessageHandler(
            filters.TEXT & filters.ChatType.GROUPS & filters.Regex(r"(?i)@all"),
            tagall_message_handler,
        ),
        group=1,
    )

    # ── Keyword filters → AI chat ──────────────────────────────────────────────
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, check_filters),   group=2)
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, ai_chat_handler), group=3)

    logger.info("Bot is running...")
    app.run_polling(allowed_updates=Update.ALL_TYPES)


if __name__ == "__main__":
    main()
