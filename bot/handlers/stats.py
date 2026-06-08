import logging
from telegram import Update
from telegram.ext import ContextTypes
import utils.storage as storage

logger = logging.getLogger(__name__)

_STATS_KEY = "mafia_stats"


def record_game_result(winner: str, players: dict) -> None:
    """
    Called at end of each Mafia game.
    winner: 'town' or 'mafia'
    players: {user_id: {id, name, role, alive}}
    """
    from handlers.mafia import ROLE_MAFIA
    for uid, player in players.items():
        user_id  = player["id"]
        role     = player["role"]
        is_mafia = role == ROLE_MAFIA

        # Use user_id as the storage key (global, not per-chat)
        data  = storage.load(user_id)
        stats = data.get(_STATS_KEY, {
            "games": 0, "wins": 0, "losses": 0,
            "mafia_games": 0, "mafia_wins": 0,
            "town_games": 0, "town_wins": 0,
            "survived": 0,
        })

        stats["games"] += 1

        if is_mafia:
            stats["mafia_games"] += 1
            if winner == "mafia":
                stats["wins"] += 1
                stats["mafia_wins"] += 1
            else:
                stats["losses"] += 1
        else:
            stats["town_games"] += 1
            if winner == "town":
                stats["wins"] += 1
                stats["town_wins"] += 1
            else:
                stats["losses"] += 1

        if player["alive"]:
            stats["survived"] += 1

        data[_STATS_KEY] = stats
        storage.save(user_id, data)


async def stats_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user

    # If replying to someone, show their stats
    msg    = update.message
    target = msg.reply_to_message.from_user if msg.reply_to_message else user

    data   = storage.load(target.id)
    stats  = data.get(_STATS_KEY)

    if not stats or stats.get("games", 0) == 0:
        if target.id == user.id:
            await msg.reply_text("📊 You haven't played any Mafia games yet!")
        else:
            await msg.reply_text(f"📊 <b>{target.first_name}</b> hasn't played any Mafia games yet!", parse_mode="HTML")
        return

    games   = stats["games"]
    wins    = stats["wins"]
    losses  = stats["losses"]
    win_pct = round(wins / games * 100) if games else 0

    mf_g = stats.get("mafia_games", 0)
    mf_w = stats.get("mafia_wins", 0)
    tw_g = stats.get("town_games", 0)
    tw_w = stats.get("town_wins", 0)
    surv = stats.get("survived", 0)

    mf_pct = round(mf_w / mf_g * 100) if mf_g else 0
    tw_pct = round(tw_w / tw_g * 100) if tw_g else 0

    name = target.first_name

    rank = (
        "👑 Legend"     if win_pct >= 80 and games >= 10 else
        "🔥 Pro"        if win_pct >= 65 and games >= 5  else
        "⚔️ Veteran"   if win_pct >= 50 and games >= 3  else
        "🌱 Rookie"     if games < 3                     else
        "😤 Struggling"
    )

    await msg.reply_text(
        f"📊 <b>{name}'s Mafia Stats</b>\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"🎭 Rank: <b>{rank}</b>\n\n"
        f"🎮 Games played: <b>{games}</b>\n"
        f"✅ Wins: <b>{wins}</b>  |  ❌ Losses: <b>{losses}</b>\n"
        f"🏆 Win rate: <b>{win_pct}%</b>\n"
        f"🛡️ Survived: <b>{surv}</b> games\n\n"
        f"🔴 As Mafia: <b>{mf_w}W / {mf_g - mf_w}L</b>"
        + (f" ({mf_pct}%)" if mf_g else "") + "\n"
        f"🔵 As Town: <b>{tw_w}W / {tw_g - tw_w}L</b>"
        + (f" ({tw_pct}%)" if tw_g else ""),
        parse_mode="HTML",
    )
