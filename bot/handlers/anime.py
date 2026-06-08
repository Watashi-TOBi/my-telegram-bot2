import logging
import httpx
from telegram import Update
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

_NEKOS_BASE = "https://nekos.best/api/v2"

_ACTIONS = {
    "hug":    ("{actor} hugs {target} 🤗",       "{actor} hugs themselves... 🤗"),
    "kiss":   ("{actor} kisses {target} 😘",      "{actor} sends a kiss to the air 💋"),
    "slap":   ("{actor} slaps {target} 😤",       "{actor} slaps themselves??"),
    "pat":    ("{actor} pats {target} 🥺",        "{actor} pats themselves 🥺"),
    "cuddle": ("{actor} cuddles with {target} 🥰", "{actor} cuddles a pillow 🥰"),
    "poke":   ("{actor} pokes {target} 👉",       "{actor} pokes the air 👉"),
    "bite":   ("{actor} bites {target} 😬",       "{actor} bites themselves??"),
    "punch":  ("{actor} punches {target} 👊",     "{actor} punches the air 👊"),
    "wink":   ("{actor} winks at {target} 😉",    "{actor} winks at the void 😉"),
    "baka":   ("{actor} calls {target} a baka 💢", "{actor} calls themselves baka 💢"),
}

_NEKOS_ENDPOINT = {
    "baka": "baka",
    "bite": "bite",
    "cuddle": "cuddle",
    "hug": "hug",
    "kiss": "kiss",
    "pat": "pat",
    "poke": "poke",
    "punch": "punch",
    "slap": "slap",
    "wink": "wink",
}


async def _get_gif(action: str) -> str | None:
    endpoint = _NEKOS_ENDPOINT.get(action)
    if not endpoint:
        return None
    try:
        async with httpx.AsyncClient(timeout=8) as c:
            r = await c.get(f"{_NEKOS_BASE}/{endpoint}")
            r.raise_for_status()
            results = r.json().get("results", [])
            if results:
                return results[0].get("url")
    except Exception as e:
        logger.warning("nekos.best error for %s: %s", action, e)
    return None


async def _anime_action(
    update: Update,
    context: ContextTypes.DEFAULT_TYPE,
    action: str,
) -> None:
    msg  = update.message
    actor_name = msg.from_user.first_name if msg.from_user else "Someone"

    template_with, template_solo = _ACTIONS[action]

    if msg.reply_to_message and msg.reply_to_message.from_user:
        target      = msg.reply_to_message.from_user
        target_name = target.first_name
        caption     = template_with.format(actor=actor_name, target=target_name)
    else:
        caption = template_solo.format(actor=actor_name)

    gif_url = await _get_gif(action)

    if gif_url:
        await msg.reply_animation(animation=gif_url, caption=caption)
    else:
        await msg.reply_text(caption)


# ── Individual command handlers ───────────────────────────────────────────────

async def hug_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _anime_action(update, context, "hug")

async def kiss_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _anime_action(update, context, "kiss")

async def slap_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _anime_action(update, context, "slap")

async def pat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _anime_action(update, context, "pat")

async def cuddle_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _anime_action(update, context, "cuddle")

async def poke_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _anime_action(update, context, "poke")

async def bite_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _anime_action(update, context, "bite")

async def punch_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _anime_action(update, context, "punch")

async def wink_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _anime_action(update, context, "wink")

async def baka_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await _anime_action(update, context, "baka")
