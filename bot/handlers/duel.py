import asyncio
import logging
import random
import time
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from telegram.constants import ChatType
from handlers.economy import get_coins, add_coins, deduct_coins, get_eco, save_eco
from handlers.shop import get_weapon_dmg, get_inv, save_inv, FOOD

logger = logging.getLogger(__name__)

_pending: dict[str, dict] = {}   # challenge_id -> data
_in_duel: set[int]        = set()  # user_ids currently in a duel
_counter = 0

def _new_id() -> str:
    global _counter
    _counter += 1
    return f"{_counter:04x}"

def _hp_bar(hp: int, max_hp: int = 100) -> str:
    filled = max(0, round(hp / max_hp * 10))
    empty  = 10 - filled
    return "█" * filled + "░" * empty

def _get_hp_bonus(user_id: int) -> int:
    """Consume cheapest available food and return HP bonus."""
    inv  = get_inv(user_id)
    food = inv.get("food", {})
    # Priority: cheapest first
    for fid in ("apple", "chicken", "steak", "medkit"):
        if food.get(fid, 0) > 0:
            food[fid] -= 1
            inv["food"] = food
            save_inv(user_id, inv)
            return FOOD[fid]["hp"]
    return 0

# ── /duel ─────────────────────────────────────────────────────────────────────

async def duel_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg  = update.message
    user = update.effective_user

    if msg.chat.type == ChatType.PRIVATE:
        await msg.reply_text("⚔️ Use /duel in a group!")
        return

    if not msg.reply_to_message:
        await msg.reply_text(
            "⚔️ <b>Duel</b>\nReply to a user and use:\n"
            "<code>/duel</code> — free duel\n"
            "<code>/duel [amount]</code> — bet coins",
            parse_mode="HTML",
        )
        return

    target = msg.reply_to_message.from_user
    if target.is_bot:
        await msg.reply_text("🤖 Bots don't duel.")
        return
    if target.id == user.id:
        await msg.reply_text("🤦 Can't duel yourself.")
        return
    if user.id in _in_duel or target.id in _in_duel:
        await msg.reply_text("⚠️ One of you is already in a duel!")
        return

    bet = 0
    if context.args:
        try:
            bet = max(0, int(context.args[0]))
        except ValueError:
            pass

    if bet > 0:
        challenger_bal = get_coins(user.id)
        if challenger_bal < bet:
            await msg.reply_text(
                f"❌ You need {bet:,} coins to bet. You only have {challenger_bal:,} 🪙"
            )
            return

    cid  = _new_id()
    _pending[cid] = {
        "challenger_id":   user.id,
        "challenger_name": user.first_name,
        "target_id":       target.id,
        "target_name":     target.first_name,
        "bet":             bet,
        "ts":              time.time(),
    }

    bet_text = f"\n💰 Bet: <b>{bet:,}</b> 🪙" if bet > 0 else ""
    kb = InlineKeyboardMarkup([[
        InlineKeyboardButton("✅ Accept", callback_data=f"duel|acc|{cid}"),
        InlineKeyboardButton("❌ Decline",callback_data=f"duel|dec|{cid}"),
    ]])
    await msg.reply_text(
        f"⚔️ <b>Duel Challenge!</b>\n\n"
        f"<b>{user.first_name}</b> challenges <b>{target.first_name}</b> to a duel!{bet_text}\n\n"
        f"<i>{target.first_name}, do you accept?</i>",
        parse_mode="HTML",
        reply_markup=kb,
    )

# ── Callback ──────────────────────────────────────────────────────────────────

async def duel_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q    = update.callback_query
    user = q.from_user
    await q.answer()

    parts  = q.data.split("|")
    action = parts[1] if len(parts) > 1 else ""
    cid    = parts[2] if len(parts) > 2 else ""

    duel = _pending.get(cid)
    if not duel:
        await q.edit_message_text("⌛ This duel challenge has expired.")
        return

    # Only the target can respond
    if user.id not in (duel["target_id"], duel["challenger_id"]):
        await q.answer("This isn't your duel!", show_alert=True)
        return

    if action == "dec":
        _pending.pop(cid, None)
        await q.edit_message_text(
            f"❌ <b>{duel['target_name']}</b> declined the duel. Coward! 🐔",
            parse_mode="HTML",
        )
        return

    if action == "acc":
        if user.id != duel["target_id"]:
            await q.answer("Only the challenged player can accept!", show_alert=True)
            return

        # Expire old challenges
        if time.time() - duel["ts"] > 90:
            _pending.pop(cid, None)
            await q.edit_message_text("⌛ Duel challenge expired.")
            return

        _pending.pop(cid, None)

        c_id   = duel["challenger_id"]
        c_name = duel["challenger_name"]
        t_id   = duel["target_id"]
        t_name = duel["target_name"]
        bet    = duel["bet"]

        if c_id in _in_duel or t_id in _in_duel:
            await q.edit_message_text("⚠️ One of you just entered another duel!")
            return

        # Check bet balances
        if bet > 0:
            if get_coins(c_id) < bet:
                await q.edit_message_text(
                    f"❌ {c_name} no longer has enough coins for the bet!"
                )
                return
            if get_coins(t_id) < bet:
                await q.edit_message_text(
                    f"❌ {t_name} doesn't have enough coins for the bet!"
                )
                return
            deduct_coins(c_id, bet)
            deduct_coins(t_id, bet)

        _in_duel.add(c_id)
        _in_duel.add(t_id)

        await q.edit_message_text(
            f"⚔️ <b>DUEL STARTED!</b>\n"
            f"<b>{c_name}</b> vs <b>{t_name}</b>",
            parse_mode="HTML",
        )

        try:
            await _run_duel(context, q.message.chat_id, c_id, c_name, t_id, t_name, bet)
        finally:
            _in_duel.discard(c_id)
            _in_duel.discard(t_id)

# ── Fight engine ──────────────────────────────────────────────────────────────

async def _run_duel(
    context,
    chat_id: int,
    a_id: int, a_name: str,
    b_id: int, b_name: str,
    bet: int,
) -> None:
    MAX_ROUNDS = 8

    a_bonus = _get_hp_bonus(a_id)
    b_bonus = _get_hp_bonus(b_id)
    a_hp    = 100 + a_bonus
    b_hp    = 100 + b_bonus
    a_max   = a_hp
    b_max   = b_hp

    a_dmg_range = get_weapon_dmg(a_id)
    b_dmg_range = get_weapon_dmg(b_id)

    def _status() -> str:
        return (
            f"❤️ <b>{a_name}</b>: {_hp_bar(a_hp, a_max)} {a_hp}/{a_max}\n"
            f"❤️ <b>{b_name}</b>: {_hp_bar(b_hp, b_max)} {b_hp}/{b_max}"
        )

    msg = await context.bot.send_message(
        chat_id=chat_id,
        text=f"⚔️ <b>Round 1 begins!</b>\n\n{_status()}",
        parse_mode="HTML",
    )

    for rnd in range(1, MAX_ROUNDS + 1):
        await asyncio.sleep(2)

        a_deal = random.randint(*a_dmg_range)
        b_deal = random.randint(*b_dmg_range)

        b_hp -= a_deal
        a_hp -= b_deal

        # Small chance to dodge
        if random.random() < 0.12:
            b_hp += a_deal  # A missed
            a_line = f"💨 <b>{a_name}</b> missed!"
        else:
            a_line = f"🔫 <b>{a_name}</b> hits <b>{b_name}</b> for <b>{a_deal}</b> dmg"

        if random.random() < 0.12:
            a_hp += b_deal  # B missed
            b_line = f"💨 <b>{b_name}</b> missed!"
        else:
            b_line = f"🔫 <b>{b_name}</b> hits <b>{a_name}</b> for <b>{b_deal}</b> dmg"

        a_hp = max(0, a_hp)
        b_hp = max(0, b_hp)

        round_text = (
            f"⚔️ <b>Round {rnd}</b>\n"
            f"{a_line}\n{b_line}\n\n"
            f"{_status()}"
        )

        await msg.edit_text(round_text, parse_mode="HTML")

        if a_hp <= 0 or b_hp <= 0:
            break

    await asyncio.sleep(1.5)

    # Determine winner
    if a_hp > b_hp:
        winner_id, winner_name = a_id, a_name
        loser_id,  loser_name  = b_id, b_name
    elif b_hp > a_hp:
        winner_id, winner_name = b_id, b_name
        loser_id,  loser_name  = a_id, a_name
    else:  # tie — refund bet, random winner for kill stat
        if bet > 0:
            add_coins(a_id, bet)
            add_coins(b_id, bet)
        await context.bot.send_message(
            chat_id=chat_id,
            text=f"🤝 <b>The duel ended in a DRAW!</b>\n\nBoth fighters are still standing!",
            parse_mode="HTML",
        )
        return

    # Pay winner
    prize = bet * 2 if bet > 0 else 0
    if prize > 0:
        new_bal = add_coins(winner_id, prize)
        prize_text = f"\n💰 <b>{winner_name}</b> wins <b>{prize:,}</b> coins! (Balance: {new_bal:,})"
    else:
        prize_text = ""

    # Increment kill count for winner
    eco = get_eco(winner_id)
    eco["kill_count"] = eco.get("kill_count", 0) + 1
    save_eco(winner_id, eco)

    await context.bot.send_message(
        chat_id=chat_id,
        text=(
            f"🏆 <b>{winner_name} WINS the duel!</b>\n"
            f"☠️ <b>{loser_name}</b> has been defeated!{prize_text}"
        ),
        parse_mode="HTML",
    )
