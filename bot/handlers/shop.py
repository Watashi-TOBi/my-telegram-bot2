import logging
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes
from handlers.economy import get_eco, save_eco, get_coins, deduct_coins, STARTING_COINS

logger = logging.getLogger(__name__)

# ── Catalogue ─────────────────────────────────────────────────────────────────

WEAPONS = {
    "glock":  {"name": "🔫 Glock 17",      "type": "Pistol",       "dmg": (8, 25),  "price": 800},
    "deagle": {"name": "🔫 Desert Eagle",   "type": "Pistol",       "dmg": (18, 38), "price": 2500},
    "mp5":    {"name": "🔫 MP5",            "type": "SMG",          "dmg": (14, 32), "price": 4000},
    "uzi":    {"name": "🔫 UZI",            "type": "SMG",          "dmg": (12, 35), "price": 5500},
    "ak47":   {"name": "🔫 AK-47",          "type": "Assault Rifle","dmg": (22, 48), "price": 8000},
    "m4a1":   {"name": "🔫 M4A1",           "type": "Assault Rifle","dmg": (25, 52), "price": 11000},
    "scar":   {"name": "🔫 SCAR-H",         "type": "Assault Rifle","dmg": (28, 58), "price": 16000},
}

FOOD = {
    "apple":   {"name": "🍎 Apple",   "hp": 25,  "price": 250},
    "chicken": {"name": "🍗 Chicken", "hp": 60,  "price": 600},
    "steak":   {"name": "🥩 Steak",   "hp": 120, "price": 1100},
    "medkit":  {"name": "💊 Medkit",  "hp": 250, "price": 2000},
}

TITLES = {
    "newbie":   {"name": "🌱 Newbie",    "price": 0},
    "warrior":  {"name": "⚔️ Warrior",   "price": 1500},
    "hunter":   {"name": "🎯 Hunter",    "price": 4000},
    "assassin": {"name": "💀 Assassin",  "price": 8000},
    "savage":   {"name": "🔥 Savage",    "price": 13000},
    "gangster": {"name": "🕶️ Gangster",  "price": 20000},
    "king":     {"name": "👑 King",      "price": 30000},
    "legend":   {"name": "🌟 Legend",    "price": 50000},
    "elite":    {"name": "💎 Elite",     "price": 80000},
}

# ── Inventory helpers ─────────────────────────────────────────────────────────

def get_inv(user_id: int) -> dict:
    eco = get_eco(user_id)
    return eco.get("inventory", {
        "weapons": [],
        "titles": ["newbie"],
        "food": {},
        "equipped_weapon": None,
        "equipped_title": "newbie",
        "bonus_hp": 0,
    })

def save_inv(user_id: int, inv: dict) -> None:
    from utils.storage import load, save
    data = load(user_id)
    eco  = data.get("economy", {"coins": STARTING_COINS})
    eco["inventory"] = inv
    data["economy"]  = eco
    save(user_id, data)

def get_weapon_dmg(user_id: int) -> tuple[int, int]:
    inv = get_inv(user_id)
    wkey = inv.get("equipped_weapon")
    if wkey and wkey in WEAPONS:
        return WEAPONS[wkey]["dmg"]
    return (5, 18)  # bare hands

def get_title(user_id: int) -> str:
    inv = get_inv(user_id)
    tkey = inv.get("equipped_title", "newbie")
    return TITLES.get(tkey, TITLES["newbie"])["name"]

# ── Keyboards ─────────────────────────────────────────────────────────────────

def _main_kb() -> InlineKeyboardMarkup:
    return InlineKeyboardMarkup([
        [InlineKeyboardButton("🔫 Weapons", callback_data="sh|w"),
         InlineKeyboardButton("🍎 Food",    callback_data="sh|f")],
        [InlineKeyboardButton("👑 Titles",  callback_data="sh|t"),
         InlineKeyboardButton("🎒 My Items",callback_data="sh|inv")],
    ])

def _back_kb() -> list:
    return [[InlineKeyboardButton("🔙 Back", callback_data="sh|main")]]

# ── /shop ─────────────────────────────────────────────────────────────────────

async def shop_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    coins = get_coins(update.effective_user.id)
    await update.message.reply_text(
        f"🏪 <b>Shop</b>\n"
        f"💰 Your balance: <b>{coins:,}</b> 🪙\n\n"
        f"Choose a category:",
        parse_mode="HTML",
        reply_markup=_main_kb(),
    )

# ── Callback dispatcher ───────────────────────────────────────────────────────

async def shop_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    q    = update.callback_query
    user = q.from_user
    data = q.data  # sh|... format
    await q.answer()

    parts = data.split("|")
    action = parts[1] if len(parts) > 1 else ""

    coins = get_coins(user.id)
    inv   = get_inv(user.id)

    # ── Main menu ──────────────────────────────────────────────────────────────
    if action == "main":
        await q.edit_message_text(
            f"🏪 <b>Shop</b>\n💰 Balance: <b>{coins:,}</b> 🪙\n\nChoose a category:",
            parse_mode="HTML",
            reply_markup=_main_kb(),
        )

    # ── Weapons list ───────────────────────────────────────────────────────────
    elif action == "w":
        owned = inv.get("weapons", [])
        rows  = []
        for wid, w in WEAPONS.items():
            lo, hi = w["dmg"]
            if wid in owned:
                rows.append([InlineKeyboardButton(
                    f"✅ {w['name']} ({w['type']}) — Equip",
                    callback_data=f"sh|ew|{wid}",
                )])
            else:
                rows.append([InlineKeyboardButton(
                    f"{w['name']} [{w['type']}] {w['price']:,}🪙 | {lo}-{hi} dmg",
                    callback_data=f"sh|bw|{wid}",
                )])
        rows += _back_kb()
        text = (
            f"🔫 <b>Weapons</b>  (Balance: {coins:,} 🪙)\n"
            f"<i>Higher-tier weapons deal more damage in duels & /kill</i>"
        )
        await q.edit_message_text(text, parse_mode="HTML",
                                  reply_markup=InlineKeyboardMarkup(rows))

    # ── Food list ──────────────────────────────────────────────────────────────
    elif action == "f":
        fstock = inv.get("food", {})
        rows   = []
        for fid, f in FOOD.items():
            qty = fstock.get(fid, 0)
            rows.append([InlineKeyboardButton(
                f"{f['name']} +{f['hp']}HP — {f['price']:,}🪙  (own: {qty})",
                callback_data=f"sh|bf|{fid}",
            )])
        rows += _back_kb()
        text = (
            f"🍎 <b>Food</b>  (Balance: {coins:,} 🪙)\n"
            f"<i>Food boosts your HP at the start of a duel.</i>"
        )
        await q.edit_message_text(text, parse_mode="HTML",
                                  reply_markup=InlineKeyboardMarkup(rows))

    # ── Titles list ────────────────────────────────────────────────────────────
    elif action == "t":
        owned   = inv.get("titles", ["newbie"])
        current = inv.get("equipped_title", "newbie")
        rows    = []
        for tid, t in TITLES.items():
            if tid in owned:
                label = f"{'✓ ' if tid == current else ''}{t['name']} — {'Equipped' if tid == current else 'Equip'}"
                rows.append([InlineKeyboardButton(label, callback_data=f"sh|et|{tid}")])
            else:
                price_txt = "FREE" if t["price"] == 0 else f"{t['price']:,}🪙"
                rows.append([InlineKeyboardButton(
                    f"{t['name']} — {price_txt}",
                    callback_data=f"sh|bt|{tid}",
                )])
        rows += _back_kb()
        text = f"👑 <b>Titles</b>  (Balance: {coins:,} 🪙)\n<i>Titles display next to your name in /bal</i>"
        await q.edit_message_text(text, parse_mode="HTML",
                                  reply_markup=InlineKeyboardMarkup(rows))

    # ── Inventory ──────────────────────────────────────────────────────────────
    elif action == "inv":
        owned_w  = inv.get("weapons", [])
        owned_t  = inv.get("titles", ["newbie"])
        food_stk = inv.get("food", {})
        eq_w     = inv.get("equipped_weapon")
        eq_t     = inv.get("equipped_title", "newbie")

        w_lines = "\n".join(
            f"  {'→ ' if wid == eq_w else ''}{ WEAPONS[wid]['name']}"
            for wid in owned_w if wid in WEAPONS
        ) or "  None"

        t_lines = "\n".join(
            f"  {'→ ' if tid == eq_t else ''}{TITLES[tid]['name']}"
            for tid in owned_t if tid in TITLES
        ) or "  None"

        f_lines = "\n".join(
            f"  {FOOD[fid]['name']} x{qty}"
            for fid, qty in food_stk.items() if qty > 0 and fid in FOOD
        ) or "  None"

        text = (
            f"🎒 <b>Your Inventory</b>\n\n"
            f"🔫 <b>Weapons</b> (→ = equipped)\n{w_lines}\n\n"
            f"👑 <b>Titles</b> (→ = equipped)\n{t_lines}\n\n"
            f"🍎 <b>Food</b>\n{f_lines}"
        )
        await q.edit_message_text(text, parse_mode="HTML",
                                  reply_markup=InlineKeyboardMarkup(_back_kb()))

    # ── Buy weapon ─────────────────────────────────────────────────────────────
    elif action == "bw" and len(parts) > 2:
        wid = parts[2]
        if wid not in WEAPONS:
            await q.answer("Unknown item.", show_alert=True); return
        w = WEAPONS[wid]
        if wid in inv.get("weapons", []):
            await q.answer("You already own this weapon!", show_alert=True); return
        ok, bal = deduct_coins(user.id, w["price"])
        if not ok:
            await q.answer(f"❌ Need {w['price']:,} coins. You have {bal:,}.", show_alert=True); return
        inv.setdefault("weapons", []).append(wid)
        # Auto-equip if no weapon equipped
        if not inv.get("equipped_weapon"):
            inv["equipped_weapon"] = wid
        save_inv(user.id, inv)
        await q.answer(f"✅ Bought {w['name']}!", show_alert=True)
        # Refresh weapons page
        await shop_callback(update, context)  # re-trigger with same action hack
        # Actually refresh manually:
        owned = inv.get("weapons", [])
        rows  = []
        for _wid, _w in WEAPONS.items():
            lo, hi = _w["dmg"]
            if _wid in owned:
                rows.append([InlineKeyboardButton(f"✅ {_w['name']} — Equip", callback_data=f"sh|ew|{_wid}")])
            else:
                rows.append([InlineKeyboardButton(
                    f"{_w['name']} [{_w['type']}] {_w['price']:,}🪙 | {lo}-{hi} dmg",
                    callback_data=f"sh|bw|{_wid}",
                )])
        rows += _back_kb()
        await q.edit_message_text(
            f"🔫 <b>Weapons</b>  (Balance: {get_coins(user.id):,} 🪙)\n✅ Purchased {w['name']}!",
            parse_mode="HTML", reply_markup=InlineKeyboardMarkup(rows),
        )

    # ── Equip weapon ───────────────────────────────────────────────────────────
    elif action == "ew" and len(parts) > 2:
        wid = parts[2]
        if wid not in inv.get("weapons", []):
            await q.answer("You don't own this weapon!", show_alert=True); return
        inv["equipped_weapon"] = wid
        save_inv(user.id, inv)
        await q.answer(f"✅ Equipped {WEAPONS[wid]['name']}!", show_alert=True)
        # Refresh
        owned = inv.get("weapons", [])
        rows  = []
        for _wid, _w in WEAPONS.items():
            lo, hi = _w["dmg"]
            if _wid in owned:
                rows.append([InlineKeyboardButton(
                    f"{'✓ ' if _wid == wid else ''}✅ {_w['name']} — Equip",
                    callback_data=f"sh|ew|{_wid}",
                )])
            else:
                rows.append([InlineKeyboardButton(
                    f"{_w['name']} [{_w['type']}] {_w['price']:,}🪙 | {lo}-{hi} dmg",
                    callback_data=f"sh|bw|{_wid}",
                )])
        rows += _back_kb()
        await q.edit_message_text(
            f"🔫 <b>Weapons</b>  (Balance: {get_coins(user.id):,} 🪙)",
            parse_mode="HTML", reply_markup=InlineKeyboardMarkup(rows),
        )

    # ── Buy food ───────────────────────────────────────────────────────────────
    elif action == "bf" and len(parts) > 2:
        fid = parts[2]
        if fid not in FOOD:
            await q.answer("Unknown item.", show_alert=True); return
        f   = FOOD[fid]
        ok, bal = deduct_coins(user.id, f["price"])
        if not ok:
            await q.answer(f"❌ Need {f['price']:,} coins. You have {bal:,}.", show_alert=True); return
        fstock = inv.setdefault("food", {})
        fstock[fid] = fstock.get(fid, 0) + 1
        inv["food"] = fstock
        save_inv(user.id, inv)
        await q.answer(f"✅ Bought {f['name']}! (+{f['hp']} HP for next duel)", show_alert=True)
        # Refresh food page
        fstock2 = inv.get("food", {})
        rows    = []
        for _fid, _f in FOOD.items():
            qty = fstock2.get(_fid, 0)
            rows.append([InlineKeyboardButton(
                f"{_f['name']} +{_f['hp']}HP — {_f['price']:,}🪙  (own: {qty})",
                callback_data=f"sh|bf|{_fid}",
            )])
        rows += _back_kb()
        await q.edit_message_text(
            f"🍎 <b>Food</b>  (Balance: {get_coins(user.id):,} 🪙)\n✅ Bought {f['name']}!",
            parse_mode="HTML", reply_markup=InlineKeyboardMarkup(rows),
        )

    # ── Buy title ──────────────────────────────────────────────────────────────
    elif action == "bt" and len(parts) > 2:
        tid = parts[2]
        if tid not in TITLES:
            await q.answer("Unknown title.", show_alert=True); return
        t = TITLES[tid]
        if tid in inv.get("titles", []):
            await q.answer("You already own this title!", show_alert=True); return
        if t["price"] > 0:
            ok, bal = deduct_coins(user.id, t["price"])
            if not ok:
                await q.answer(f"❌ Need {t['price']:,} coins. You have {bal:,}.", show_alert=True); return
        inv.setdefault("titles", ["newbie"]).append(tid)
        inv["equipped_title"] = tid  # auto-equip purchased title
        save_inv(user.id, inv)
        await q.answer(f"✅ Bought & equipped {t['name']}!", show_alert=True)
        # Refresh titles page
        owned2  = inv.get("titles", ["newbie"])
        current = inv.get("equipped_title", "newbie")
        rows    = []
        for _tid, _t in TITLES.items():
            if _tid in owned2:
                label = f"{'✓ ' if _tid == current else ''}{_t['name']} — {'Equipped' if _tid == current else 'Equip'}"
                rows.append([InlineKeyboardButton(label, callback_data=f"sh|et|{_tid}")])
            else:
                price_txt = "FREE" if _t["price"] == 0 else f"{_t['price']:,}🪙"
                rows.append([InlineKeyboardButton(f"{_t['name']} — {price_txt}", callback_data=f"sh|bt|{_tid}")])
        rows += _back_kb()
        await q.edit_message_text(
            f"👑 <b>Titles</b>  (Balance: {get_coins(user.id):,} 🪙)\n✅ Equipped {t['name']}!",
            parse_mode="HTML", reply_markup=InlineKeyboardMarkup(rows),
        )

    # ── Equip title ────────────────────────────────────────────────────────────
    elif action == "et" and len(parts) > 2:
        tid = parts[2]
        if tid not in inv.get("titles", []):
            await q.answer("You don't own this title!", show_alert=True); return
        inv["equipped_title"] = tid
        save_inv(user.id, inv)
        await q.answer(f"✅ Equipped {TITLES[tid]['name']}!", show_alert=True)
        # Refresh titles page
        owned2  = inv.get("titles", ["newbie"])
        rows    = []
        for _tid, _t in TITLES.items():
            if _tid in owned2:
                label = f"{'✓ ' if _tid == tid else ''}{_t['name']} — {'Equipped' if _tid == tid else 'Equip'}"
                rows.append([InlineKeyboardButton(label, callback_data=f"sh|et|{_tid}")])
            else:
                price_txt = "FREE" if _t["price"] == 0 else f"{_t['price']:,}🪙"
                rows.append([InlineKeyboardButton(f"{_t['name']} — {price_txt}", callback_data=f"sh|bt|{_tid}")])
        rows += _back_kb()
        await q.edit_message_text(
            f"👑 <b>Titles</b>  (Balance: {get_coins(user.id):,} 🪙)",
            parse_mode="HTML", reply_markup=InlineKeyboardMarkup(rows),
        )
