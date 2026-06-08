import io
import logging
import re
import textwrap

import httpx
from PIL import Image, ImageDraw, ImageFont, ImageFilter
from telegram import Update, InputFile, InputSticker
from telegram.ext import ContextTypes

logger = logging.getLogger(__name__)

_FONT_BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
_FONT_REG  = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"

# Palette
_BG_TOP    = (13,  13,  26)
_BG_BOT    = (26,  20,  50)
_ACCENT    = (138, 87, 222)
_NAME_CLR  = (210, 175, 255, 255)
_TEXT_CLR  = (235, 235, 245, 255)
_QUOTE_CLR = (90,  60, 150, 140)
_DIM       = (100, 90, 130, 180)


def _strip_emoji(text: str) -> str:
    return re.sub(
        r"[\U00010000-\U0010ffff\U0001F600-\U0001F64F\U0001F300-\U0001F5FF"
        r"\U0001F680-\U0001F6FF\U0001F1E0-\U0001F1FF\u2600-\u26FF\u2700-\u27BF]+",
        "", text, flags=re.UNICODE,
    ).strip()


def _gradient_bg(size: tuple) -> Image.Image:
    W, H = size
    base = Image.new("RGB", (W, H), _BG_TOP)
    for y in range(H):
        t = y / H
        r = int(_BG_TOP[0] + (_BG_BOT[0] - _BG_TOP[0]) * t)
        g = int(_BG_TOP[1] + (_BG_BOT[1] - _BG_TOP[1]) * t)
        b = int(_BG_TOP[2] + (_BG_BOT[2] - _BG_TOP[2]) * t)
        base.paste(Image.new("RGB", (W, 1), (r, g, b)), (0, y))
    return base


def _circle_crop(img: Image.Image, size: int) -> Image.Image:
    img = img.convert("RGBA").resize((size, size), Image.LANCZOS)
    mask = Image.new("L", (size, size), 0)
    ImageDraw.Draw(mask).ellipse((0, 0, size, size), fill=255)
    out = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    out.paste(img, mask=mask)
    return out


def _initials_avatar(name: str, size: int) -> Image.Image:
    """Generate a colored circle with initials when no profile photo exists."""
    COLORS = [
        (138, 87, 222), (220, 80, 120), (80, 180, 140),
        (220, 140, 40), (60, 140, 220), (180, 80, 180),
    ]
    color = COLORS[hash(name) % len(COLORS)]
    img   = Image.new("RGBA", (size, size), (0, 0, 0, 0))
    draw  = ImageDraw.Draw(img)
    draw.ellipse((0, 0, size, size), fill=color)

    initials = "".join(w[0].upper() for w in name.split()[:2]) or "?"
    try:
        font = ImageFont.truetype(_FONT_BOLD, size // 3)
    except Exception:
        font = ImageFont.load_default()

    bbox = draw.textbbox((0, 0), initials, font=font)
    tw   = bbox[2] - bbox[0]
    th   = bbox[3] - bbox[1]
    draw.text(((size - tw) // 2, (size - th) // 2 - 2), initials, font=font, fill=(255, 255, 255, 255))
    return img


async def _fetch_avatar(bot, user_id: int, size: int) -> Image.Image | None:
    try:
        photos = await bot.get_user_profile_photos(user_id, limit=1)
        if photos.total_count > 0:
            file_obj = await photos.photos[0][-1].get_file()
            async with httpx.AsyncClient(timeout=8) as client:
                resp = await client.get(file_obj.file_path)
                resp.raise_for_status()
                avatar = Image.open(io.BytesIO(resp.content))
                return _circle_crop(avatar, size)
    except Exception as e:
        logger.debug("Avatar fetch failed: %s", e)
    return None


def _make_quote_sticker(
    sender_name: str,
    text: str,
    avatar: Image.Image | None,
) -> io.BytesIO:
    W, H = 512, 512

    try:
        fn  = ImageFont.truetype(_FONT_BOLD, 26)
        ft  = ImageFont.truetype(_FONT_REG,  22)
        fq  = ImageFont.truetype(_FONT_BOLD, 96)
        fsm = ImageFont.truetype(_FONT_REG,  16)
    except Exception:
        fn = ft = fq = fsm = ImageFont.load_default()

    # Background
    bg   = _gradient_bg((W, H))
    img  = Image.new("RGBA", (W, H), (0, 0, 0, 0))
    img.paste(bg)
    draw = ImageDraw.Draw(img)

    # Card
    pad = 18
    draw.rounded_rectangle([pad, pad, W - pad, H - pad], radius=28, fill=(20, 16, 40, 230))

    # Accent stripe
    bx = pad + 12
    draw.rectangle([bx, pad + 12, bx + 5, H - pad - 12], fill=_ACCENT)

    # Opening quote mark (decorative, top-right)
    draw.text((W - pad - 100, pad - 12), "\u201c", font=fq, fill=_QUOTE_CLR)

    # Avatar
    AVA = 68
    ava_x = bx + 14
    ava_y = pad + 16

    if avatar:
        img.paste(avatar, (ava_x, ava_y), mask=avatar)
    else:
        name_clean = _strip_emoji(sender_name) or sender_name
        ava_img    = _initials_avatar(name_clean, AVA)
        img.paste(ava_img, (ava_x, ava_y), mask=ava_img)

    # Avatar border ring
    ring_draw = ImageDraw.Draw(img)
    ring_draw.ellipse(
        [ava_x - 2, ava_y - 2, ava_x + AVA + 2, ava_y + AVA + 2],
        outline=_ACCENT, width=2,
    )

    # Sender name (right of avatar)
    name_x = ava_x + AVA + 14
    name_y = ava_y + (AVA // 2) - 16
    name_clean = _strip_emoji(sender_name) or sender_name
    draw.text((name_x, name_y), name_clean, font=fn, fill=_NAME_CLR)

    # Divider under avatar row
    div_y = ava_y + AVA + 14
    draw.line([bx + 14, div_y, W - pad - 18, div_y], fill=(70, 55, 110, 160), width=1)

    # Message body
    body    = _strip_emoji(text) or text
    wrapped = textwrap.fill(body, width=28)
    text_y  = div_y + 16
    draw.multiline_text(
        (bx + 14, text_y),
        wrapped,
        font=ft,
        fill=_TEXT_CLR,
        spacing=10,
    )

    # Closing quote mark (bottom-right)
    draw.text((W - pad - 78, H - pad - 100), "\u201d", font=fq, fill=_QUOTE_CLR)

    # Bottom label: "via @bot" style subtle text
    draw.text((bx + 14, H - pad - 26), "✦ quoted", font=fsm, fill=_DIM)

    buf = io.BytesIO()
    img.save(buf, format="WEBP", lossless=True)
    buf.seek(0)
    return buf


async def quote_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg = update.message
    if not msg.reply_to_message:
        await msg.reply_text("💬 Reply to a message to turn it into a quote sticker!")
        return

    replied = msg.reply_to_message
    text    = replied.text or replied.caption
    if not text:
        await msg.reply_text("❌ That message has no text to quote.")
        return

    sender      = replied.from_user
    sender_name = sender.full_name if sender else "Unknown"
    sender_id   = sender.id if sender else None

    loading = await msg.reply_text("✨ Creating quote sticker...")

    try:
        # Fetch avatar
        avatar = None
        if sender_id:
            avatar = await _fetch_avatar(context.bot, sender_id, 68)

        if avatar is None and sender_name:
            avatar = _initials_avatar(_strip_emoji(sender_name) or sender_name, 68)

        sticker_buf = _make_quote_sticker(sender_name, text, avatar)
        await loading.delete()
        await context.bot.send_sticker(
            chat_id=msg.chat_id,
            sticker=InputFile(sticker_buf, filename="sticker.webp"),
            reply_to_message_id=msg.message_id,
        )
    except Exception as e:
        logger.error("Quote sticker error: %s", e, exc_info=True)
        try:
            await loading.edit_text(f"❌ Failed to create sticker: {e}")
        except Exception:
            pass


# ── Kang ─────────────────────────────────────────────────────────────────────

def _sticker_format(sticker) -> str:
    if sticker.is_animated:
        return "animated"
    if sticker.is_video:
        return "video"
    return "static"


async def kang_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    msg  = update.message
    user = msg.from_user
    bot  = context.bot

    if not msg.reply_to_message or not msg.reply_to_message.sticker:
        await msg.reply_text("🎨 Reply to a sticker to kang (steal) it into your pack!")
        return

    sticker  = msg.reply_to_message.sticker
    fmt      = _sticker_format(sticker)
    set_name = f"k{user.id}_by_{bot.username}"[:64]
    set_title = f"{user.first_name}'s Stash"
    emoji_list = [sticker.emoji] if sticker.emoji else ["🎭"]

    sf   = await sticker.get_file()
    data = bytes(await sf.download_as_bytearray())

    input_s = InputSticker(sticker=data, emoji_list=emoji_list, format=fmt)
    status  = await msg.reply_text("🔄 Kanging sticker...")

    async def _send_success(created: bool) -> None:
        label    = "New pack created" if created else "Added to your pack"
        pack_url = f"https://t.me/addstickers/{set_name}"
        try:
            ss = await bot.get_sticker_set(set_name)
            await msg.reply_sticker(ss.stickers[-1].file_id)
        except Exception:
            pass
        await status.edit_text(
            f"✅ {label}!\n📦 <a href='{pack_url}'>Open sticker pack</a>",
            parse_mode="HTML",
            disable_web_page_preview=True,
        )

    try:
        await bot.add_sticker_to_set(user_id=user.id, name=set_name, sticker=input_s)
        await _send_success(created=False)
        return
    except Exception as e:
        logger.info("add_sticker_to_set failed (%s) — trying create", e)

    try:
        await bot.create_new_sticker_set(
            user_id=user.id, name=set_name, title=set_title, stickers=[input_s],
        )
        await _send_success(created=True)
    except Exception as e2:
        err = str(e2)
        logger.error("create_new_sticker_set failed: %s", err)
        if any(x in err for x in ("PEER_ID_INVALID", "Forbidden", "bot was blocked",
                                   "chat not found", "have no access")):
            await status.edit_text(
                f"⚠️ Start me in DM first so I can create your sticker pack!\n"
                f"👉 <a href='https://t.me/{bot.username}?start=kang'>Open DM</a>",
                parse_mode="HTML",
            )
        else:
            await status.edit_text(f"❌ Could not kang: {err}")
