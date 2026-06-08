import logging
import random
from collections import defaultdict
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.error import Forbidden, BadRequest

logger = logging.getLogger(__name__)

# ── Constants ─────────────────────────────────────────────────────────────────

ROLE_MAFIA   = "mafia"
ROLE_CITIZEN = "citizen"
ROLE_SHERIFF = "sheriff"
ROLE_DOCTOR  = "doctor"

ROLE_EMOJI = {
    ROLE_MAFIA:   "🔴",
    ROLE_CITIZEN: "🔵",
    ROLE_SHERIFF: "🟡",
    ROLE_DOCTOR:  "🟢",
}

ROLE_NAMES = {
    ROLE_MAFIA:   "Mafia",
    ROLE_CITIZEN: "Citizen",
    ROLE_SHERIFF: "Sheriff",
    ROLE_DOCTOR:  "Doctor",
}

MIN_PLAYERS = 4
MAX_PLAYERS = 20

# In-memory game state: {chat_id: game_dict}
_games: dict[int, dict] = {}

# ── Role assignment ───────────────────────────────────────────────────────────

def _assign_roles(player_ids: list) -> dict:
    n = len(player_ids)
    mafia_count = 1 if n < 7 else (2 if n < 10 else 3)

    roles = [ROLE_MAFIA] * mafia_count
    roles.append(ROLE_SHERIFF)
    if n >= 5:
        roles.append(ROLE_DOCTOR)
    roles.extend([ROLE_CITIZEN] * (n - len(roles)))

    shuffled = player_ids[:]
    random.shuffle(shuffled)
    return dict(zip(shuffled, roles))

# ── Helpers ───────────────────────────────────────────────────────────────────

def _alive(game: dict) -> dict:
    return {uid: p for uid, p in game["players"].items() if p["alive"]}

def _by_role(game: dict, role: str, alive_only: bool = True) -> dict:
    base = _alive(game) if alive_only else game["players"]
    return {uid: p for uid, p in base.items() if p["role"] == role}

def _check_win(game: dict) -> str | None:
    alive = _alive(game)
    mafia_n = sum(1 for p in alive.values() if p["role"] == ROLE_MAFIA)
    town_n  = sum(1 for p in alive.values() if p["role"] != ROLE_MAFIA)
    if mafia_n == 0:
        return "town"
    if mafia_n >= town_n:
        return "mafia"
    return None

async def _try_dm(context, user_id: int, **kwargs) -> bool:
    try:
        await context.bot.send_message(chat_id=user_id, **kwargs)
        return True
    except (Forbidden, BadRequest):
        return False

def _alive_keyboard(game: dict, chat_id: int, action: str, exclude: set = None) -> InlineKeyboardMarkup:
    exclude = exclude or set()
    return InlineKeyboardMarkup([
        [InlineKeyboardButton(p["name"], callback_data=f"mg_{action}_{chat_id}_{uid}")]
        for uid, p in _alive(game).items() if uid not in exclude
    ])

# ── Night phase ───────────────────────────────────────────────────────────────

async def _start_night(context, chat_id: int) -> None:
    game = _games[chat_id]
    game["state"]        = "night"
    game["round"]       += 1
    game["night_kill"]   = None
    game["night_save"]   = None
    game["night_check"]  = None
    game["pending"]      = set()

    round_n = game["round"]
    alive   = _alive(game)

    await context.bot.send_message(
        chat_id=chat_id,
        text=f"🌙 <b>Night {round_n} falls...</b>\n\nThe town goes to sleep. The Mafia is plotting... 🔴\n<i>Check your DMs to take your night action.</i>",
        parse_mode="HTML",
    )

    mafia   = _by_role(game, ROLE_MAFIA)
    sheriff = _by_role(game, ROLE_SHERIFF)
    doctor  = _by_role(game, ROLE_DOCTOR)

    # ── Mafia DM ──
    if mafia:
        game["pending"].add("mafia")
        non_mafia_kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(p["name"], callback_data=f"mg_kill_{chat_id}_{uid}")]
            for uid, p in alive.items() if uid not in mafia
        ])
        failed = []
        for uid, p in mafia.items():
            allies = [mp["name"] for mid, mp in mafia.items() if mid != uid]
            ally_line = f"\n👥 Allies: {', '.join(allies)}" if allies else ""
            ok = await _try_dm(
                context, uid,
                text=f"🌙 <b>Night {round_n}</b>{ally_line}\n\n🔴 Pick your target to eliminate:",
                reply_markup=non_mafia_kb,
                parse_mode="HTML",
            )
            if not ok:
                failed.append(p["name"])
        if failed:
            await context.bot.send_message(chat_id=chat_id, text=f"⚠️ Couldn't DM {', '.join(failed)}. They need to /start the bot in DM first.")
            # If ALL mafia unreachable, skip mafia action
            if len(failed) == len(mafia):
                game["pending"].discard("mafia")

    # ── Sheriff DM ──
    if sheriff:
        game["pending"].add("sheriff")
        for uid, p in sheriff.items():
            kb = _alive_keyboard(game, chat_id, "check", exclude={uid})
            ok = await _try_dm(
                context, uid,
                text=f"🌙 <b>Night {round_n}</b>\n\n🟡 Who do you want to investigate?",
                reply_markup=kb,
                parse_mode="HTML",
            )
            if not ok:
                game["pending"].discard("sheriff")

    # ── Doctor DM ──
    if doctor:
        game["pending"].add("doctor")
        for uid, p in doctor.items():
            kb = _alive_keyboard(game, chat_id, "save")
            ok = await _try_dm(
                context, uid,
                text=f"🌙 <b>Night {round_n}</b>\n\n🟢 Who do you want to protect tonight?",
                reply_markup=kb,
                parse_mode="HTML",
            )
            if not ok:
                game["pending"].discard("doctor")

    if not game["pending"]:
        await _resolve_night(context, chat_id)


async def _resolve_night(context, chat_id: int) -> None:
    game       = _games.get(chat_id)
    if not game:
        return

    killed_id  = game["night_kill"]
    saved_id   = game["night_save"]

    if killed_id and killed_id == saved_id:
        msg = "☀️ <b>Morning arrives...</b>\n\n✨ The Doctor saved someone — <b>nobody died tonight!</b>"
    elif killed_id and killed_id in game["players"] and game["players"][killed_id]["alive"]:
        victim = game["players"][killed_id]
        victim["alive"] = False
        role_name  = ROLE_NAMES[victim["role"]]
        role_emoji = ROLE_EMOJI[victim["role"]]
        msg = (
            f"☀️ <b>Morning arrives...</b>\n\n"
            f"💀 <b>{victim['name']}</b> was found dead!\n"
            f"They were a <b>{role_emoji} {role_name}</b>."
        )
    else:
        msg = "☀️ <b>Morning arrives...</b>\n\nThe night passed quietly. Nobody died."

    await context.bot.send_message(chat_id=chat_id, text=msg, parse_mode="HTML")

    winner = _check_win(game)
    if winner:
        await _end_game(context, chat_id, winner)
        return

    await _start_day(context, chat_id)


# ── Day phase ─────────────────────────────────────────────────────────────────

async def _start_day(context, chat_id: int) -> None:
    game = _games[chat_id]
    game["state"]     = "day"
    game["day_votes"] = {}

    alive      = _alive(game)
    alive_list = "\n".join(f"• {p['name']}" for p in alive.values())
    vote_kb    = InlineKeyboardMarkup([
        [InlineKeyboardButton(f"⚖️ {p['name']}", callback_data=f"mg_vote_{chat_id}_{uid}")]
        for uid, p in alive.items()
    ])

    msg = await context.bot.send_message(
        chat_id=chat_id,
        text=(
            f"☀️ <b>Day {game['round']} — Town Meeting</b>\n\n"
            f"👥 Alive ({len(alive)}):\n{alive_list}\n\n"
            f"🗳 <b>Vote to eliminate a suspect!</b>\n"
            f"Each player votes once. Majority wins."
        ),
        reply_markup=vote_kb,
        parse_mode="HTML",
    )
    game["vote_msg_id"] = msg.message_id


async def _resolve_day(context, chat_id: int) -> None:
    game  = _games.get(chat_id)
    if not game:
        return
    votes = game["day_votes"]

    if not votes:
        await context.bot.send_message(
            chat_id=chat_id,
            text="🕊️ <b>No votes cast.</b> The town lets the suspect go...",
            parse_mode="HTML",
        )
        await _start_night(context, chat_id)
        return

    tally: dict = defaultdict(int)
    for target_id in votes.values():
        tally[target_id] += 1

    max_v = max(tally.values())
    top   = [uid for uid, v in tally.items() if v == max_v]

    if len(top) > 1:
        names = [game["players"][uid]["name"] for uid in top]
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"🤝 <b>It's a tie!</b> ({', '.join(names)} — {max_v} vote(s) each)\nNo one is eliminated today.",
            parse_mode="HTML",
        )
    else:
        elim_id = top[0]
        victim  = game["players"][elim_id]
        victim["alive"] = False
        await context.bot.send_message(
            chat_id=chat_id,
            text=(
                f"⚖️ <b>The town has decided!</b>\n\n"
                f"💀 <b>{victim['name']}</b> was eliminated with <b>{max_v} vote(s)</b>.\n"
                f"They were a <b>{ROLE_EMOJI[victim['role']]} {ROLE_NAMES[victim['role']]}</b>."
            ),
            parse_mode="HTML",
        )

    winner = _check_win(game)
    if winner:
        await _end_game(context, chat_id, winner)
        return

    await _start_night(context, chat_id)


# ── End game ──────────────────────────────────────────────────────────────────

async def _end_game(context, chat_id: int, winner: str) -> None:
    game = _games.pop(chat_id, {})
    players = game.get("players", {})

    if winner == "town":
        header = "🎉 <b>Town Wins!</b>\nThe Mafia has been wiped out. Peace is restored!"
    else:
        header = "💀 <b>Mafia Wins!</b>\nThe Mafia now controls the town. Nobody is safe..."

    reveal = "\n".join(
        f"{ROLE_EMOJI[p['role']]} {p['name']} — {ROLE_NAMES[p['role']]}"
        + ("" if p["alive"] else " 💀")
        for p in players.values()
    )

    await context.bot.send_message(
        chat_id=chat_id,
        text=f"{header}\n\n<b>🎭 Role Reveal:</b>\n{reveal}",
        parse_mode="HTML",
    )

    # Record stats for all players
    try:
        from handlers.stats import record_game_result
        record_game_result(winner, players)
    except Exception as e:
        logger.warning("Failed to record game stats: %s", e)


# ── Command handlers ──────────────────────────────────────────────────────────

async def startgame_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    user = update.effective_user

    if chat.type == "private":
        await update.message.reply_text("Start a game in a group chat!")
        return

    if chat.id in _games:
        await update.message.reply_text("A game is already active here! Use /endgame to cancel it first.")
        return

    _games[chat.id] = {
        "state":       "lobby",
        "host":        user.id,
        "players":     {user.id: {"id": user.id, "name": user.first_name, "role": None, "alive": True}},
        "round":       0,
        "night_kill":  None,
        "night_save":  None,
        "night_check": None,
        "pending":     set(),
        "day_votes":   {},
        "vote_msg_id": None,
    }

    await update.message.reply_text(
        f"🎭 <b>Mafia Game — Lobby Open!</b>\n\n"
        f"👑 Host: <b>{user.first_name}</b>\n"
        f"👥 Players (1/{MAX_PLAYERS}): {user.first_name}\n\n"
        f"• Use /join to join the lobby\n"
        f"• Need at least {MIN_PLAYERS} players\n"
        f"• Host uses /startmafia when ready\n"
        f"• /gamerules to learn how to play",
        parse_mode="HTML",
    )


async def join_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    user = update.effective_user

    if chat.type == "private":
        await update.message.reply_text("Join a game in a group chat!")
        return

    if chat.id not in _games:
        await update.message.reply_text("No lobby active here. Use /startgame to open one!")
        return

    game = _games[chat.id]

    if game["state"] != "lobby":
        await update.message.reply_text("The game has already started. Wait for the next round!")
        return

    if user.id in game["players"]:
        await update.message.reply_text("You're already in the lobby!")
        return

    if len(game["players"]) >= MAX_PLAYERS:
        await update.message.reply_text(f"Lobby is full ({MAX_PLAYERS} players max)!")
        return

    game["players"][user.id] = {"id": user.id, "name": user.first_name, "role": None, "alive": True}
    count = len(game["players"])
    names = ", ".join(p["name"] for p in game["players"].values())
    ready = count >= MIN_PLAYERS

    await update.message.reply_text(
        f"✅ <b>{user.first_name}</b> joined!\n\n"
        f"👥 Players ({count}/{MAX_PLAYERS}): {names}\n\n"
        f"{'✅ Ready! Host can use /startmafia' if ready else f'⏳ Need {MIN_PLAYERS - count} more player(s)...'}",
        parse_mode="HTML",
    )


async def flee_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    user = update.effective_user

    if chat.id not in _games:
        await update.message.reply_text("No game active here.")
        return

    game = _games[chat.id]

    if user.id not in game["players"]:
        await update.message.reply_text("You're not in the game!")
        return

    if game["state"] != "lobby":
        await update.message.reply_text("Can't leave mid-game. Use /endgame to cancel the whole game.")
        return

    del game["players"][user.id]
    await update.message.reply_text(f"👋 <b>{user.first_name}</b> left the lobby.", parse_mode="HTML")

    if not game["players"]:
        del _games[chat.id]
        await update.message.reply_text("Lobby closed — everyone left.")
        return

    if game["host"] == user.id:
        new_host_id      = next(iter(game["players"]))
        game["host"]     = new_host_id
        new_host_name    = game["players"][new_host_id]["name"]
        await update.message.reply_text(f"👑 <b>{new_host_name}</b> is now the host.", parse_mode="HTML")


async def startmafia_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    user = update.effective_user

    if chat.id not in _games:
        await update.message.reply_text("No lobby active! Use /startgame first.")
        return

    game = _games[chat.id]

    if game["state"] != "lobby":
        await update.message.reply_text("The game has already started!")
        return

    if user.id != game["host"]:
        member = await context.bot.get_chat_member(chat.id, user.id)
        if member.status not in ("administrator", "creator"):
            await update.message.reply_text("Only the host or a group admin can start the game!")
            return

    n = len(game["players"])
    if n < MIN_PLAYERS:
        await update.message.reply_text(f"Need at least {MIN_PLAYERS} players to start. Currently: {n}")
        return

    # Assign roles
    role_map = _assign_roles(list(game["players"].keys()))
    for uid, role in role_map.items():
        game["players"][uid]["role"] = role

    names = ", ".join(p["name"] for p in game["players"].values())
    await update.message.reply_text(
        f"🎭 <b>The Mafia Game begins!</b>\n\n"
        f"👥 {n} players: {names}\n\n"
        f"<i>Roles are being sent to your DMs...\n"
        f"Make sure you've started @{context.bot.username} in DM first!</i>",
        parse_mode="HTML",
    )

    # Send role DMs
    failed = []
    for uid, player in game["players"].items():
        role      = player["role"]
        role_desc = {
            ROLE_MAFIA:   "Each night, eliminate a town member. Stay hidden during the day.",
            ROLE_SHERIFF: "Each night, investigate one player to see if they're Mafia.",
            ROLE_DOCTOR:  "Each night, protect one player from being killed.",
            ROLE_CITIZEN: "Use the day phase to debate and vote out the Mafia.",
        }[role]

        ok = await _try_dm(
            context, uid,
            text=(
                f"🎭 <b>Your Role: {ROLE_EMOJI[role]} {ROLE_NAMES[role]}</b>\n\n"
                f"{role_desc}\n\n"
                f"<i>Game is in the group. Wait for the night phase!</i>"
            ),
            parse_mode="HTML",
        )
        if not ok:
            failed.append(player["name"])

    if failed:
        await context.bot.send_message(
            chat_id=chat.id,
            text=f"⚠️ Couldn't DM: {', '.join(failed)}\nThey should start the bot in DM (/start) then use /resend.",
        )

    await _start_night(context, chat.id)


async def resend_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Resend role DM to the requesting player."""
    chat = update.effective_chat
    user = update.effective_user

    if chat.id not in _games:
        await update.message.reply_text("No game active here.")
        return

    game = _games[chat.id]

    if game["state"] == "lobby":
        await update.message.reply_text("The game hasn't started yet!")
        return

    if user.id not in game["players"]:
        await update.message.reply_text("You're not in this game.")
        return

    player = game["players"][user.id]
    role   = player["role"]
    role_desc = {
        ROLE_MAFIA:   "Each night, eliminate a town member. Stay hidden during the day.",
        ROLE_SHERIFF: "Each night, investigate one player to see if they're Mafia.",
        ROLE_DOCTOR:  "Each night, protect one player from being killed.",
        ROLE_CITIZEN: "Use the day phase to debate and vote out the Mafia.",
    }[role]

    ok = await _try_dm(
        context, user.id,
        text=(
            f"🎭 <b>Your Role: {ROLE_EMOJI[role]} {ROLE_NAMES[role]}</b>\n\n"
            f"{role_desc}\n\n"
            f"<i>Game is ongoing in the group!</i>"
        ),
        parse_mode="HTML",
    )

    if ok:
        await update.message.reply_text("✅ Role sent to your DM!")
    else:
        await update.message.reply_text("❌ Couldn't DM you. Please start the bot in DM first: open a chat with me and press Start.")


async def players_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat

    if chat.id not in _games:
        await update.message.reply_text("No game active here.")
        return

    game  = _games[chat.id]
    alive = _alive(game)
    dead  = {uid: p for uid, p in game["players"].items() if not p["alive"]}

    text = f"👥 <b>Players — {game['state'].title()} Phase</b>\n\n"
    text += f"✅ Alive ({len(alive)}):\n"
    text += ("\n".join(f"• {p['name']}" for p in alive.values()) or "None")

    if dead:
        text += f"\n\n💀 Eliminated ({len(dead)}):\n"
        text += "\n".join(
            f"• {p['name']} — {ROLE_EMOJI[p['role']]} {ROLE_NAMES[p['role']]}"
            for p in dead.values()
        )

    await update.message.reply_text(text, parse_mode="HTML")


async def endgame_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    user = update.effective_user

    if chat.id not in _games:
        await update.message.reply_text("No game running here.")
        return

    game   = _games[chat.id]
    member = await context.bot.get_chat_member(chat.id, user.id)

    if user.id != game["host"] and member.status not in ("administrator", "creator"):
        await update.message.reply_text("Only the host or a group admin can end the game.")
        return

    del _games[chat.id]
    await update.message.reply_text("🛑 <b>Game cancelled.</b>", parse_mode="HTML")


async def skip_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    """Host/admin skips the current phase."""
    chat = update.effective_chat
    user = update.effective_user

    if chat.id not in _games:
        return

    game   = _games[chat.id]
    member = await context.bot.get_chat_member(chat.id, user.id)

    if user.id != game["host"] and member.status not in ("administrator", "creator"):
        await update.message.reply_text("Only the host or an admin can skip the phase.")
        return

    if game["state"] == "night":
        game["pending"].clear()
        await update.message.reply_text("⏭️ Night phase skipped by host.")
        await _resolve_night(context, chat.id)
    elif game["state"] == "day":
        await update.message.reply_text("⏭️ Voting phase skipped by host.")
        await _resolve_day(context, chat.id)
    else:
        await update.message.reply_text("Nothing to skip right now.")


async def gamerules_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "🎭 <b>Mafia — How to Play</b>\n\n"
        "<b>Roles:</b>\n"
        "🔴 <b>Mafia</b> — kill one town member each night\n"
        "🟡 <b>Sheriff</b> — investigate one player each night\n"
        "🟢 <b>Doctor</b> — protect one player each night\n"
        "🔵 <b>Citizen</b> — vote wisely during the day\n\n"
        "<b>Phases:</b>\n"
        "🌙 <b>Night</b> — Mafia, Sheriff & Doctor act via DM\n"
        "☀️ <b>Day</b> — everyone votes to eliminate a suspect\n\n"
        "<b>Win conditions:</b>\n"
        "🏘 Town wins when all Mafia are eliminated\n"
        "💀 Mafia wins when they equal or outnumber Town\n\n"
        "<b>Commands:</b>\n"
        "/startgame — open a lobby\n"
        "/join — join the lobby\n"
        "/flee — leave the lobby\n"
        "/startmafia — begin the game (host)\n"
        "/resend — resend your role to DM\n"
        "/players — show who's alive\n"
        "/skip — force-skip current phase (host/admin)\n"
        "/endgame — cancel the game (host/admin)\n"
        "/gamerules — show this message",
        parse_mode="HTML",
    )


# ── Callback handler ──────────────────────────────────────────────────────────

async def mafia_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query  = update.callback_query
    data   = query.data  # mg_<action>_<chat_id>_<target_id>

    # Split only 3 times to handle negative chat_ids (e.g. mg_kill_-100123_456)
    parts = data.split("_", 3)
    if len(parts) != 4:
        await query.answer()
        return

    _, action, raw_chat, raw_target = parts

    try:
        chat_id   = int(raw_chat)
        target_id = int(raw_target)
    except ValueError:
        await query.answer()
        return

    voter_id = query.from_user.id

    if chat_id not in _games:
        await query.answer("This game has already ended.", show_alert=True)
        try:
            await query.edit_message_reply_markup(reply_markup=None)
        except BadRequest:
            pass
        return

    game = _games[chat_id]

    # ── Mafia kill ────────────────────────────────────────────────────────────
    if action == "kill":
        if game["state"] != "night":
            await query.answer("It's not night time!", show_alert=True)
            return
        if voter_id not in game["players"] or game["players"][voter_id]["role"] != ROLE_MAFIA:
            await query.answer("You're not Mafia!", show_alert=True)
            return
        if target_id not in game["players"] or not game["players"][target_id]["alive"]:
            await query.answer("Invalid target.", show_alert=True)
            return

        game["night_kill"] = target_id
        tname = game["players"][target_id]["name"]
        await query.answer(f"🔴 Target locked: {tname}", show_alert=True)
        try:
            await query.edit_message_text(
                f"🔴 You chose to eliminate <b>{tname}</b>.\n<i>Waiting for other roles...</i>",
                parse_mode="HTML",
            )
        except BadRequest:
            pass

        game["pending"].discard("mafia")
        if not game["pending"]:
            await _resolve_night(context, chat_id)

    # ── Doctor save ───────────────────────────────────────────────────────────
    elif action == "save":
        if game["state"] != "night":
            await query.answer("It's not night time!", show_alert=True)
            return
        if voter_id not in game["players"] or game["players"][voter_id]["role"] != ROLE_DOCTOR:
            await query.answer("You're not the Doctor!", show_alert=True)
            return
        if target_id not in game["players"] or not game["players"][target_id]["alive"]:
            await query.answer("Invalid target.", show_alert=True)
            return

        game["night_save"] = target_id
        tname = game["players"][target_id]["name"]
        await query.answer(f"🟢 You're protecting {tname}!", show_alert=True)
        try:
            await query.edit_message_text(
                f"🟢 You chose to protect <b>{tname}</b> tonight.",
                parse_mode="HTML",
            )
        except BadRequest:
            pass

        game["pending"].discard("doctor")
        if not game["pending"]:
            await _resolve_night(context, chat_id)

    # ── Sheriff check ─────────────────────────────────────────────────────────
    elif action == "check":
        if game["state"] != "night":
            await query.answer("It's not night time!", show_alert=True)
            return
        if voter_id not in game["players"] or game["players"][voter_id]["role"] != ROLE_SHERIFF:
            await query.answer("You're not the Sheriff!", show_alert=True)
            return
        if target_id not in game["players"] or not game["players"][target_id]["alive"]:
            await query.answer("Invalid target.", show_alert=True)
            return

        target    = game["players"][target_id]
        is_mafia  = target["role"] == ROLE_MAFIA
        result    = "🔴 MAFIA!" if is_mafia else "🔵 Not Mafia (innocent)"
        await query.answer(f"Investigation: {target['name']} is {result}", show_alert=True)
        try:
            await query.edit_message_text(
                f"🟡 Investigation result for <b>{target['name']}</b>:\n{result}",
                parse_mode="HTML",
            )
        except BadRequest:
            pass

        game["night_check"] = target_id
        game["pending"].discard("sheriff")
        if not game["pending"]:
            await _resolve_night(context, chat_id)

    # ── Day vote ──────────────────────────────────────────────────────────────
    elif action == "vote":
        if game["state"] != "day":
            await query.answer("Voting is not active right now!", show_alert=True)
            return
        if voter_id not in game["players"]:
            await query.answer("You're not in this game!", show_alert=True)
            return
        if not game["players"][voter_id]["alive"]:
            await query.answer("Dead players can't vote!", show_alert=True)
            return
        if voter_id == target_id:
            await query.answer("You can't vote for yourself!", show_alert=True)
            return
        if target_id not in game["players"] or not game["players"][target_id]["alive"]:
            await query.answer("Invalid target.", show_alert=True)
            return
        if voter_id in game["day_votes"]:
            prev_name = game["players"][game["day_votes"][voter_id]]["name"]
            await query.answer(f"You already voted for {prev_name}!", show_alert=True)
            return

        game["day_votes"][voter_id] = target_id
        tname     = game["players"][target_id]["name"]
        alive     = _alive(game)
        vote_count = len(game["day_votes"])
        alive_count = len(alive)

        # Build tally
        tally: dict = defaultdict(int)
        for t in game["day_votes"].values():
            tally[t] += 1
        tally_lines = "\n".join(
            f"• {game['players'][uid]['name']}: {v} vote(s)"
            for uid, v in sorted(tally.items(), key=lambda x: -x[1])
        )

        await query.answer(f"✅ You voted for {tname}!", show_alert=True)

        new_kb = InlineKeyboardMarkup([
            [InlineKeyboardButton(f"⚖️ {p['name']}", callback_data=f"mg_vote_{chat_id}_{uid}")]
            for uid, p in alive.items()
        ])
        try:
            await query.edit_message_text(
                f"☀️ <b>Day {game['round']} — Voting</b>\n\n"
                f"📊 Votes ({vote_count}/{alive_count}):\n{tally_lines}\n\n"
                f"🗳 Cast your vote:",
                reply_markup=new_kb,
                parse_mode="HTML",
            )
        except BadRequest:
            pass

        if vote_count >= alive_count:
            await _resolve_day(context, chat_id)

    else:
        await query.answer()
