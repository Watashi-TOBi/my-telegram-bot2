import random
from telegram import Update
from telegram.ext import ContextTypes

from utils.members import get_members


# ── Love ──────────────────────────────────────────────────────────────────────

def _love_score(name1: str, name2: str) -> int:
    """Deterministic score so the same pair always gets the same result."""
    key  = tuple(sorted([name1.lower(), name2.lower()]))
    seed = hash(key) & 0x7FFFFFFF
    rng  = random.Random(seed)
    return rng.randint(0, 100)


def _build_bar(pct: int, width: int = 10) -> str:
    filled = round(pct / 100 * width)
    return "█" * filled + "░" * (width - filled)


def _verdict(pct: int) -> tuple[str, str]:
    if pct >= 90:
        return "💞", "A match made in heaven!"
    if pct >= 75:
        return "❤️", "Strong connection — great match!"
    if pct >= 55:
        return "💓", "Good chemistry, keep it going!"
    if pct >= 35:
        return "💛", "Some potential, but needs effort."
    if pct >= 15:
        return "💔", "It's a tough road ahead..."
    return "😬", "Opposites... not attracting here."


async def love_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    args = context.args
    if not args or len(args) < 2:
        await update.message.reply_text(
            "💘 Usage: <code>/love Name1 Name2</code>",
            parse_mode="HTML",
        )
        return

    name1 = args[0]
    name2 = args[1]
    pct   = _love_score(name1, name2)
    bar   = _build_bar(pct)
    emoji, verdict = _verdict(pct)

    text = (
        f"💘 <b>Love Calculator</b> 💘\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"👤 <b>{name1}</b>\n"
        f"       ❤️\n"
        f"👤 <b>{name2}</b>\n"
        f"━━━━━━━━━━━━━━━━\n"
        f"<code>[{bar}]</code>  <b>{pct}%</b>\n\n"
        f"{emoji}  <i>{verdict}</i>"
    )

    await update.message.reply_text(text, parse_mode="HTML")


# ── Crush ─────────────────────────────────────────────────────────────────────

async def crush_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg  = update.message
    chat = update.effective_chat

    if chat.type not in ("group", "supergroup"):
        await msg.reply_text("💘 This command only works in groups!")
        return

    if not msg.reply_to_message:
        await msg.reply_text("💘 Reply to someone's message to reveal their secret crush!")
        return

    target = msg.reply_to_message.from_user
    bot    = context.bot

    # ── Bot special case ──────────────────────────────────────────────────────
    if target.id == bot.id:
        await msg.reply_text(
            f"💘 <b>{bot.first_name}</b> Cʀᴜꜱʜ Iꜱ Death\n"
            f"Crush level: ∞ ❤️",
            parse_mode="HTML",
        )
        return

    # ── Pick a random known group member ──────────────────────────────────────
    members    = get_members(chat.id)
    candidates = {
        uid: name for uid, name in members.items()
        if int(uid) != target.id and int(uid) != msg.from_user.id
    }

    if candidates:
        crush_name = random.choice(list(candidates.values()))
    else:
        crush_name = "Someone Special 👀"

    level  = random.randint(0, 100)
    target_link = f'<a href="tg://user?id={target.id}">{target.first_name}</a>'

    await msg.reply_text(
        f"💘 {target_link} Sᴇᴄʀᴇᴛ Cʀᴜꜱʜ Iꜱ <b>{crush_name}</b>\n"
        f"Crush level: {level}% ❤️",
        parse_mode="HTML",
    )
