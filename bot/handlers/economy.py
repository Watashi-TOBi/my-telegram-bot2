import logging
import os
import json
import random
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ChatType
import utils.storage as storage

logger = logging.getLogger(__name__)

STARTING_COINS   = 500
DAILY_AMOUNT     = 1000
WEEKLY_AMOUNT    = 5000
MONTHLY_AMOUNT   = 10000
DAILY_COOLDOWN   = 86400
WEEKLY_COOLDOWN  = 86400 * 7
MONTHLY_COOLDOWN = 86400 * 30
_ECO_KEY         = "economy"

# ── Core helpers ──────────────────────────────────────────────────────────────

def get_eco(user_id: int) -> dict:
    data = storage.load(user_id)
    return data.get(_ECO_KEY, {"coins": STARTING_COINS})

def save_eco(user_id: int, eco: dict) -> None:
    data = storage.load(user_id)
    data[_ECO_KEY] = eco
    storage.save(user_id, data)

def get_coins(user_id: int) -> int:
    return get_eco(user_id).get("coins", STARTING_COINS)

def add_coins(user_id: int, amount: int) -> int:
    eco = get_eco(user_id)
    eco["coins"] = max(0, eco.get("coins", STARTING_COINS) + amount)
    save_eco(user_id, eco)
    return eco["coins"]

def deduct_coins(user_id: int, amount: int) -> tuple[bool, int]:
    eco = get_eco(user_id)
    current = eco.get("coins", STARTING_COINS)
    if current < amount:
        return False, current
    eco["coins"] = current - amount
    save_eco(user_id, eco)
    return True, eco["coins"]

def _fmt_cd(secs: int) -> str:
    h, r = divmod(secs, 3600)
    m    = r // 60
    if h >= 24:
        d, h = divmod(h, 24)
        return f"{d}d {h}h {m}m"
    return f"{h}h {m}m"

# ── Global scan helper ────────────────────────────────────────────────────────

def _scan_all_users() -> list[dict]:
    """Return list of {id, name, coins, kills} for every user data file."""
    data_dir = os.path.join(os.path.dirname(__file__), "..", "data")
    results  = []
    try:
        for fname in os.listdir(data_dir):
            if not fname.endswith(".json"):
                continue
            try:
                uid = int(fname[:-5])
            except ValueError:
                continue
            if uid < 0:
                continue  # skip group/chat files
            try:
                with open(os.path.join(data_dir, fname)) as f:
                    raw = json.load(f)
                eco = raw.get(_ECO_KEY, {})
                if not eco:
                    continue
                results.append({
                    "id":    uid,
                    "coins": eco.get("coins", STARTING_COINS),
                    "kills": eco.get("kill_count", 0),
                })
            except Exception:
                continue
    except FileNotFoundError:
        pass
    return results

# ── /bal ──────────────────────────────────────────────────────────────────────

async def bal_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg    = update.message
    target = msg.reply_to_message.from_user if msg.reply_to_message else update.effective_user

    eco    = get_eco(target.id)
    coins  = eco.get("coins", STARTING_COINS)
    kills  = eco.get("kill_count", 0)
    inv    = eco.get("inventory", {})
    title  = _title_name(inv.get("equipped_title", "newbie"))
    weapon = _weapon_name(inv.get("equipped_weapon"))

    rank = (
        "🏆 Rich"    if coins >= 10000 else
        "💰 Wealthy" if coins >= 3000  else
        "🪙 Average" if coins >= 500   else
        "😢 Broke"
    )

    await msg.reply_text(
        f"👤 <b>{target.first_name}'s Profile</b>\n"
        f"━━━━━━━━━━━━━━\n"
        f"{title}\n"
        f"🔫 Weapon: {weapon}\n"
        f"💀 Kills: <b>{kills}</b>\n"
        f"🪙 Coins: <b>{coins:,}</b>  {rank}",
        parse_mode="HTML",
    )

def _title_name(tkey: str) -> str:
    try:
        from handlers.shop import TITLES
        return TITLES.get(tkey, TITLES["newbie"])["name"]
    except Exception:
        return "🌱 Newbie"

def _weapon_name(wkey) -> str:
    if not wkey:
        return "🤜 Fists"
    try:
        from handlers.shop import WEAPONS
        return WEAPONS.get(wkey, {}).get("name", "🤜 Fists")
    except Exception:
        return "🤜 Fists"

# ── Bonus commands ─────────────────────────────────────────────────────────────

async def daily_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    eco  = get_eco(user.id)
    now  = time.time()
    diff = now - eco.get("last_daily", 0)
    if diff < DAILY_COOLDOWN:
        return await update.message.reply_text(
            f"⏳ Daily already claimed!\nCome back in <b>{_fmt_cd(int(DAILY_COOLDOWN - diff))}</b>.",
            parse_mode="HTML",
        )
    eco["coins"]      = eco.get("coins", STARTING_COINS) + DAILY_AMOUNT
    eco["last_daily"] = now
    save_eco(user.id, eco)
    await update.message.reply_text(
        f"🎁 <b>Daily reward!</b>  +{DAILY_AMOUNT:,} 🪙\n"
        f"Balance: <b>{eco['coins']:,}</b>",
        parse_mode="HTML",
    )

async def weekly_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    eco  = get_eco(user.id)
    now  = time.time()
    diff = now - eco.get("last_weekly", 0)
    if diff < WEEKLY_COOLDOWN:
        return await update.message.reply_text(
            f"⏳ Weekly already claimed!\nCome back in <b>{_fmt_cd(int(WEEKLY_COOLDOWN - diff))}</b>.",
            parse_mode="HTML",
        )
    eco["coins"]       = eco.get("coins", STARTING_COINS) + WEEKLY_AMOUNT
    eco["last_weekly"] = now
    save_eco(user.id, eco)
    await update.message.reply_text(
        f"🗓️ <b>Weekly reward!</b>  +{WEEKLY_AMOUNT:,} 🪙\n"
        f"Balance: <b>{eco['coins']:,}</b>",
        parse_mode="HTML",
    )

async def monthly_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    eco  = get_eco(user.id)
    now  = time.time()
    diff = now - eco.get("last_monthly", 0)
    if diff < MONTHLY_COOLDOWN:
        return await update.message.reply_text(
            f"⏳ Monthly already claimed!\nCome back in <b>{_fmt_cd(int(MONTHLY_COOLDOWN - diff))}</b>.",
            parse_mode="HTML",
        )
    eco["coins"]        = eco.get("coins", STARTING_COINS) + MONTHLY_AMOUNT
    eco["last_monthly"] = now
    save_eco(user.id, eco)
    await update.message.reply_text(
        f"📅 <b>Monthly reward!</b>  +{MONTHLY_AMOUNT:,} 🪙\n"
        f"Balance: <b>{eco['coins']:,}</b>",
        parse_mode="HTML",
    )

# ── /kill ─────────────────────────────────────────────────────────────────────

_KILL_W = [
    "{k} pulled out a {weapon} and dropped {t}. Headshot! 🎯",
    "{k} sniped {t} from 500m with a {weapon}. 💀",
    "{k} rushed {t} with a {weapon}. No mercy! ⚔️",
    "{k} challenged {t} to a duel and finished it with their {weapon}. 🏆",
    "{k} ambushed {t} with a {weapon}. Didn't see it coming! 😈",
]
_KILL_L = [
    "{k} tried to attack {t} but the {weapon} jammed. 😂",
    "{k} missed every shot with their {weapon}. Embarrassing. 🙈",
    "{k} slipped and dropped their {weapon}. {t} laughed. 😭",
]

async def kill_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg  = update.message
    user = update.effective_user
    if msg.chat.type == ChatType.PRIVATE:
        return await msg.reply_text("Use /kill in a group!")
    if not msg.reply_to_message:
        return await msg.reply_text("💀 Reply to someone to kill them!")
    target = msg.reply_to_message.from_user
    if target.id == user.id:
        return await msg.reply_text("☠️ You can't kill yourself!")
    if target.is_bot:
        return await msg.reply_text("🤖 Bots are immortal.")

    from handlers.shop import get_inv, WEAPONS
    inv     = get_inv(user.id)
    wkey    = inv.get("equipped_weapon")
    wname   = WEAPONS[wkey]["name"] if wkey and wkey in WEAPONS else "fists"
    # Better weapon = better success rate
    success_rate = 0.55
    if wkey:
        dmg_max = WEAPONS[wkey]["dmg"][1]
        success_rate = min(0.80, 0.55 + dmg_max / 200)

    success = random.random() < success_rate
    reward  = random.randint(50, 150)

    if success:
        earned = add_coins(user.id, reward)
        deduct_coins(target.id, reward // 2)
        eco = get_eco(user.id)
        eco["kill_count"] = eco.get("kill_count", 0) + 1
        save_eco(user.id, eco)
        txt = random.choice(_KILL_W).format(k=user.first_name, t=target.first_name, weapon=wname)
        await msg.reply_text(
            f"{txt}\n\n💰 Earned <b>{reward}</b> coins! (Balance: {earned:,})",
            parse_mode="HTML",
        )
    else:
        lost   = random.randint(20, 70)
        _, bal = deduct_coins(user.id, lost)
        txt    = random.choice(_KILL_L).format(k=user.first_name, t=target.first_name, weapon=wname)
        await msg.reply_text(
            f"{txt}\n\n💸 Lost <b>{lost}</b> coins. (Balance: {bal:,})",
            parse_mode="HTML",
        )

# ── /rob ──────────────────────────────────────────────────────────────────────

_ROB_W = [
    "{r} sneaked into {t}'s house at 3 AM and swiped the wallet 🕵️",
    "{r} pickpocketed {t} in broad daylight. Smooth. 🤏",
    "{r} hacked {t}'s crypto wallet. Big brain. 💻",
]
_ROB_L = [
    "{r} got caught robbing {t} and paid a fine! 🚔",
    "{r} tripped the alarm at {t}'s place. 🚨",
    "{r} tried to pickpocket {t} but got caught. 😂",
]

async def rob_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg  = update.message
    user = update.effective_user
    if msg.chat.type == ChatType.PRIVATE:
        return await msg.reply_text("Use /rob in a group!")
    if not msg.reply_to_message:
        return await msg.reply_text("🤏 Reply to someone to rob them!")
    target = msg.reply_to_message.from_user
    if target.id == user.id or target.is_bot:
        return await msg.reply_text("Can't rob that.")
    target_coins = get_coins(target.id)
    if target_coins < 50:
        return await msg.reply_text(f"💀 {target.first_name} is already broke. Not worth it.")
    if random.random() < 0.40:
        stolen  = max(30, min(int(target_coins * random.uniform(0.15, 0.30)), 600))
        deduct_coins(target.id, stolen)
        new_bal = add_coins(user.id, stolen)
        txt     = random.choice(_ROB_W).format(r=user.first_name, t=target.first_name)
        await msg.reply_text(
            f"{txt}\n\n💰 Stole <b>{stolen}</b> coins! (Balance: {new_bal:,})",
            parse_mode="HTML",
        )
    else:
        fine   = random.randint(80, 200)
        _, bal = deduct_coins(user.id, fine)
        txt    = random.choice(_ROB_L).format(r=user.first_name, t=target.first_name)
        await msg.reply_text(
            f"{txt}\n\n💸 Fined <b>{fine}</b> coins. (Balance: {bal:,})",
            parse_mode="HTML",
        )

# ── Leaderboard helpers ───────────────────────────────────────────────────────

_MEDALS = ["🥇","🥈","🥉","4️⃣","5️⃣","6️⃣","7️⃣","8️⃣","9️⃣","🔟"]

def _lb_keyboard(mode: str, scope: str, chat_id: int) -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([[
        InlineKeyboardButton(
            f"{'✓ ' if scope == 'g' else ''}🌍 Global",
            callback_data=f"lb|{mode}|g|{chat_id}",
        ),
        InlineKeyboardButton(
            f"{'✓ ' if scope == 'c' else ''}👥 This Group",
            callback_data=f"lb|{mode}|c|{chat_id}",
        ),
    ]])

def _build_money_group(chat_id: int) -> str:
    from utils.members import get_members
    members = get_members(chat_id)
    if not members:
        return "No members tracked yet."
    board = sorted(
        [(name, get_coins(int(uid))) for uid, name in members.items()],
        key=lambda x: x[1], reverse=True,
    )[:10]
    return "\n".join(f"{_MEDALS[i]} <b>{n}</b> — {c:,} 🪙" for i, (n, c) in enumerate(board))

def _build_money_global() -> str:
    users = sorted(_scan_all_users(), key=lambda x: x["coins"], reverse=True)[:10]
    if not users:
        return "No data yet."
    lines = []
    for i, u in enumerate(users):
        try:
            data = storage.load(u["id"])
            name = data.get("economy", {}).get("first_name", f"User {u['id']}")
        except Exception:
            name = f"User {u['id']}"
        lines.append(f"{_MEDALS[i]} <b>{name}</b> — {u['coins']:,} 🪙")
    return "\n".join(lines)

def _build_kills_group(chat_id: int) -> str:
    from utils.members import get_members
    members = get_members(chat_id)
    if not members:
        return "No members tracked yet."
    board = sorted(
        [(name, get_eco(int(uid)).get("kill_count", 0)) for uid, name in members.items()],
        key=lambda x: x[1], reverse=True,
    )[:10]
    return "\n".join(f"{_MEDALS[i]} <b>{n}</b> — {k} ☠️" for i, (n, k) in enumerate(board))

def _build_kills_global() -> str:
    users = sorted(_scan_all_users(), key=lambda x: x["kills"], reverse=True)[:10]
    if not users:
        return "No data yet."
    lines = []
    for i, u in enumerate(users):
        try:
            data = storage.load(u["id"])
            name = data.get("economy", {}).get("first_name", f"User {u['id']}")
        except Exception:
            name = f"User {u['id']}"
        lines.append(f"{_MEDALS[i]} <b>{name}</b> — {u['kills']} ☠️")
    return "\n".join(lines)

# ── /leaderboard ──────────────────────────────────────────────────────────────

async def leaderboard_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    if chat.type == ChatType.PRIVATE:
        rows = _build_money_global()
        await update.message.reply_text(
            f"💰 <b>Top Richest — Global</b>\n━━━━━━━━━━━━━━\n{rows}",
            parse_mode="HTML",
        )
        return
    rows = _build_money_group(chat.id)
    await update.message.reply_text(
        f"💰 <b>Top Richest — This Group</b>\n━━━━━━━━━━━━━━\n{rows}",
        parse_mode="HTML",
        reply_markup=_lb_keyboard("m", "c", chat.id),
    )

# ── /topkills ─────────────────────────────────────────────────────────────────

async def topkills_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    chat = update.effective_chat
    if chat.type == ChatType.PRIVATE:
        rows = _build_kills_global()
        await update.message.reply_text(
            f"☠️ <b>Top Killers — Global</b>\n━━━━━━━━━━━━━━\n{rows}",
            parse_mode="HTML",
        )
        return
    rows = _build_kills_group(chat.id)
    await update.message.reply_text(
        f"☠️ <b>Top Killers — This Group</b>\n━━━━━━━━━━━━━━\n{rows}",
        parse_mode="HTML",
        reply_markup=_lb_keyboard("k", "c", chat.id),
    )

# ── Leaderboard callback ──────────────────────────────────────────────────────

async def lb_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q = update.callback_query
    await q.answer()
    parts = q.data.split("|")  # lb|mode|scope|chat_id
    if len(parts) < 4:
        return
    _, mode, scope, chat_id_str = parts
    try:
        chat_id = int(chat_id_str)
    except ValueError:
        return

    if mode == "m":
        rows  = _build_money_group(chat_id) if scope == "c" else _build_money_global()
        label = "This Group" if scope == "c" else "Global"
        title = f"💰 <b>Top Richest — {label}</b>"
    else:
        rows  = _build_kills_group(chat_id) if scope == "c" else _build_kills_global()
        label = "This Group" if scope == "c" else "Global"
        title = f"☠️ <b>Top Killers — {label}</b>"

    await q.edit_message_text(
        f"{title}\n━━━━━━━━━━━━━━\n{rows}",
        parse_mode="HTML",
        reply_markup=_lb_keyboard(mode, scope, chat_id),
    )
