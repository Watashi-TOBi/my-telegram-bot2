import logging
import os
from collections import defaultdict, deque
from groq import AsyncGroq
from telegram import Update
from telegram.ext import ContextTypes
from telegram.constants import ChatType, ChatAction

logger = logging.getLogger(__name__)

GROQ_API_KEY = os.environ.get("GROQ_API_KEY")
_client = AsyncGroq(api_key=GROQ_API_KEY) if GROQ_API_KEY else None

_SYSTEM_PROMPT = """
You are a chill, witty person chatting on Telegram — not an AI assistant.

Rules you must follow without exception:
- Never say you're an AI, a bot, a language model, or anything like that. If someone asks, deflect casually ("lol why would I be a bot") or change the subject.
- Talk like a real person texting a friend: short sentences, casual grammar, occasional slang. No bullet points, no numbered lists, no headers.
- Don't be overly positive or use filler phrases like "Certainly!", "Of course!", "Great question!", "Absolutely!" — real people don't talk like that.
- Match the user's energy. If they're funny, be funny back. If they're serious, tone it down. If they use their language or slang, mirror it naturally.
- Keep replies concise — most should be 1-3 sentences. Don't dump a wall of text unless you really need to.
- Swear occasionally if the vibe calls for it, but don't overdo it.
- Have opinions. Take sides. Be a little opinionated rather than always sitting on the fence.
- If you don't know something, say so like a human would ("honestly no clue", "no idea tbh").
- Never use emojis excessively. One at most per message, and only when it genuinely fits.
- Remember what was said earlier in the conversation and refer back naturally when it's relevant.
- Address the person by their name when it feels natural, not every single message.
""".strip()

_HISTORY_SIZE = 20
_history: dict[int, deque] = defaultdict(lambda: deque(maxlen=_HISTORY_SIZE))


def _should_respond(update: Update, bot_username: str, bot_id: int) -> tuple[bool, str]:
    """Only reply in DMs, when @mentioned, or when user replies to the bot's message."""
    if not update.message:
        return False, ""

    text = (update.message.text or update.message.caption or "").strip()
    chat_type = update.effective_chat.type

    # Always reply in private / DM
    if chat_type == ChatType.PRIVATE:
        return True, text

    # In groups: only reply when @mentioned
    mention = f"@{bot_username}"
    if mention.lower() in text.lower():
        clean = text.replace(mention, "").replace(mention.lower(), "").strip()
        return True, clean or text

    # In groups: only reply when someone replies to one of the bot's messages
    reply = update.message.reply_to_message
    if reply and reply.from_user and reply.from_user.id == bot_id:
        return True, text

    return False, ""


async def _ask_groq(chat_id: int, user_text: str, sender_name: str, chat_title: str | None) -> str:
    if not _client:
        raise RuntimeError("Groq client not initialized")

    history = _history[chat_id]

    # Build system prompt with context about who the bot is talking to
    context_note = f"You're talking to {sender_name}"
    if chat_title:
        context_note += f" in a group called '{chat_title}'"
    context_note += "."

    system = _SYSTEM_PROMPT + f"\n\nContext: {context_note}"

    messages = [{"role": "system", "content": system}]
    messages.extend(list(history))
    messages.append({"role": "user", "content": user_text})

    chat = await _client.chat.completions.create(
        model="llama-3.3-70b-versatile",
        messages=messages,
        max_tokens=300,
        temperature=0.85,
    )
    reply = chat.choices[0].message.content.strip()

    history.append({"role": "user",      "content": f"{sender_name}: {user_text}"})
    history.append({"role": "assistant", "content": reply})

    return reply


async def ai_chat_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    if not _client:
        return

    bot_username = context.bot.username
    bot_id       = context.bot.id

    should_respond, user_text = _should_respond(update, bot_username, bot_id)
    if not should_respond:
        return

    sender_name = update.effective_user.first_name or "there"
    chat_title  = update.effective_chat.title if update.effective_chat.type != ChatType.PRIVATE else None

    if not user_text:
        await update.message.reply_text(f"wassup {sender_name}")
        return

    await context.bot.send_chat_action(
        chat_id=update.effective_chat.id,
        action=ChatAction.TYPING,
    )

    chat_id = update.effective_chat.id

    try:
        reply = await _ask_groq(chat_id, user_text, sender_name, chat_title)
        if not reply:
            raise ValueError("Empty response from Groq")
        await update.message.reply_text(reply)
    except Exception as e:
        logger.error("Groq error: %s", e, exc_info=True)
        await update.message.reply_text("ugh, something broke on my end. try again")
