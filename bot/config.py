import os

TELEGRAM_TOKEN = os.environ.get("TELEGRAM_TOKEN") or os.environ.get("BOT_TOKEN")
AI_API_KEY = os.environ.get("AI_API_KEY")

if not TELEGRAM_TOKEN:
    raise RuntimeError("TELEGRAM_TOKEN environment variable is not set")
if not AI_API_KEY:
    import logging
    logging.getLogger(__name__).warning("AI_API_KEY is not set — AI chat disabled")

SUPPORT_URL = os.environ.get("SUPPORT_URL", "https://t.me/bored_hub")
OWNER_URL   = os.environ.get("OWNER_URL",   "https://t.me/Yours_Rasm")
SOURCE_URL  = os.environ.get("SOURCE_URL",  "https://github.com/")
