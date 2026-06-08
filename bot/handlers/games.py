import asyncio
import logging
import random
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatType
from handlers.economy import get_coins, add_coins, deduct_coins

logger = logging.getLogger(__name__)

GAME_COST = 20   # default entry fee
BET_MIN   = 10
BET_MAX   = 2000

# ── /bet ──────────────────────────────────────────────────────────────────────

async def bet_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg  = update.message
    user = update.effective_user

    if not context.args:
        await msg.reply_text(
            "🎲 Usage: <code>/bet [amount]</code>\n"
            f"Min: {BET_MIN} 🪙  |  Max: {BET_MAX} 🪙",
            parse_mode="HTML",
        )
        return

    try:
        amount = int(context.args[0])
    except ValueError:
        await msg.reply_text("❌ Enter a valid number. e.g. <code>/bet 100</code>", parse_mode="HTML")
        return

    if amount < BET_MIN or amount > BET_MAX:
        await msg.reply_text(f"❌ Bet must be between {BET_MIN} and {BET_MAX} coins.")
        return

    ok, bal = deduct_coins(user.id, amount)
    if not ok:
        await msg.reply_text(f"❌ Not enough coins! You have <b>{bal:,}</b> 🪙", parse_mode="HTML")
        return

    # Roll two dice — user vs bot
    user_roll = random.randint(1, 6)
    bot_roll  = random.randint(1, 6)

    dice_msg = await msg.reply_dice(emoji="🎲")
    await asyncio.sleep(3)

    if user_roll > bot_roll:
        new_bal = add_coins(user.id, amount * 2)
        result  = f"🎉 <b>You win {amount} coins!</b>"
    elif user_roll < bot_roll:
        result  = f"😢 <b>You lost {amount} coins.</b>"
        new_bal = get_coins(user.id)
    else:
        new_bal = add_coins(user.id, amount)  # refund on tie
        result  = f"🤝 <b>It's a tie! Coins refunded.</b>"

    await msg.reply_text(
        f"🎲 Your roll: <b>{user_roll}</b>  vs  Bot: <b>{bot_roll}</b>\n\n"
        f"{result}\n🪙 Balance: <b>{new_bal:,}</b>",
        parse_mode="HTML",
    )

# ── /football ─────────────────────────────────────────────────────────────────

async def football_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg  = update.message
    user = update.effective_user

    ok, bal = deduct_coins(user.id, GAME_COST)
    if not ok:
        await msg.reply_text(f"❌ Need {GAME_COST} coins to play. You have <b>{bal:,}</b> 🪙", parse_mode="HTML")
        return

    dice_msg = await msg.reply_dice(emoji="⚽")
    await asyncio.sleep(3)

    value = dice_msg.dice.value  # 1-5
    if value >= 4:
        prize   = GAME_COST * 3
        new_bal = add_coins(user.id, prize)
        result  = f"⚽ <b>GOAL!</b> You scored! +{prize} coins 🎉"
    else:
        new_bal = get_coins(user.id)
        result  = f"😬 <b>Missed!</b> Better luck next time. (-{GAME_COST} coins)"

    await msg.reply_text(f"{result}\n🪙 Balance: <b>{new_bal:,}</b>", parse_mode="HTML")

# ── /basket ───────────────────────────────────────────────────────────────────

async def basket_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg  = update.message
    user = update.effective_user

    ok, bal = deduct_coins(user.id, GAME_COST)
    if not ok:
        await msg.reply_text(f"❌ Need {GAME_COST} coins to play. You have <b>{bal:,}</b> 🪙", parse_mode="HTML")
        return

    dice_msg = await msg.reply_dice(emoji="🏀")
    await asyncio.sleep(3)

    value = dice_msg.dice.value  # 1-5
    if value >= 4:
        prize   = GAME_COST * 3
        new_bal = add_coins(user.id, prize)
        result  = f"🏀 <b>SWISH!</b> It's in! +{prize} coins 🎉"
    else:
        new_bal = get_coins(user.id)
        result  = f"😬 <b>Missed the hoop!</b> (-{GAME_COST} coins)"

    await msg.reply_text(f"{result}\n🪙 Balance: <b>{new_bal:,}</b>", parse_mode="HTML")

# ── /bowling ──────────────────────────────────────────────────────────────────

async def bowling_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg  = update.message
    user = update.effective_user

    ok, bal = deduct_coins(user.id, GAME_COST)
    if not ok:
        await msg.reply_text(f"❌ Need {GAME_COST} coins to play. You have <b>{bal:,}</b> 🪙", parse_mode="HTML")
        return

    dice_msg = await msg.reply_dice(emoji="🎳")
    await asyncio.sleep(3)

    value = dice_msg.dice.value  # 1-6
    if value == 6:
        prize   = GAME_COST * 4
        new_bal = add_coins(user.id, prize)
        result  = f"🎳 <b>STRIKE!</b> All pins down! +{prize} coins 🎉"
    elif value >= 4:
        prize   = GAME_COST * 2
        new_bal = add_coins(user.id, prize)
        result  = f"🎳 <b>Spare!</b> Most pins hit. +{prize} coins"
    else:
        new_bal = get_coins(user.id)
        result  = f"😬 <b>Gutter ball!</b> (-{GAME_COST} coins)"

    await msg.reply_text(f"{result}\n🪙 Balance: <b>{new_bal:,}</b>", parse_mode="HTML")

# ── /dart ─────────────────────────────────────────────────────────────────────

async def dart_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg  = update.message
    user = update.effective_user

    ok, bal = deduct_coins(user.id, GAME_COST)
    if not ok:
        await msg.reply_text(f"❌ Need {GAME_COST} coins to play. You have <b>{bal:,}</b> 🪙", parse_mode="HTML")
        return

    dice_msg = await msg.reply_dice(emoji="🎯")
    await asyncio.sleep(3)

    value = dice_msg.dice.value  # 1-6
    if value == 6:
        prize   = GAME_COST * 5
        new_bal = add_coins(user.id, prize)
        result  = f"🎯 <b>BULLSEYE!</b> Dead center! +{prize} coins 🎉"
    elif value >= 4:
        prize   = GAME_COST * 2
        new_bal = add_coins(user.id, prize)
        result  = f"🎯 <b>Close hit!</b> Inner ring. +{prize} coins"
    else:
        new_bal = get_coins(user.id)
        result  = f"😬 <b>Missed the board!</b> (-{GAME_COST} coins)"

    await msg.reply_text(f"{result}\n🪙 Balance: <b>{new_bal:,}</b>", parse_mode="HTML")

# ── /slot ─────────────────────────────────────────────────────────────────────

SLOT_COST = 30

async def slot_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg  = update.message
    user = update.effective_user

    ok, bal = deduct_coins(user.id, SLOT_COST)
    if not ok:
        await msg.reply_text(f"❌ Need {SLOT_COST} coins to spin. You have <b>{bal:,}</b> 🪙", parse_mode="HTML")
        return

    dice_msg = await msg.reply_dice(emoji="🎰")
    await asyncio.sleep(3)

    value = dice_msg.dice.value  # 1-64

    # Jackpot = 64 (777), near-jackpot = 59-63, win = 22+, lose = rest
    if value == 64:
        prize   = SLOT_COST * 20
        new_bal = add_coins(user.id, prize)
        result  = f"🎰 <b>JACKPOT! 7️⃣7️⃣7️⃣</b>\n💥 You hit the jackpot! +{prize} coins! 🤑"
    elif value >= 50:
        prize   = SLOT_COST * 5
        new_bal = add_coins(user.id, prize)
        result  = f"🎰 <b>Big win!</b> Three of a kind! +{prize} coins 🎉"
    elif value >= 30:
        prize   = SLOT_COST * 2
        new_bal = add_coins(user.id, prize)
        result  = f"🎰 <b>Small win!</b> Two matched! +{prize} coins"
    else:
        new_bal = get_coins(user.id)
        result  = f"🎰 <b>No match.</b> Better luck next time. (-{SLOT_COST} coins)"

    await msg.reply_text(f"{result}\n🪙 Balance: <b>{new_bal:,}</b>", parse_mode="HTML")
