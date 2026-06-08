from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import ContextTypes

HELP_TEXT = """
📖 <b>Full Command Guide</b>
━━━━━━━━━━━━━━━━━━

💰 <b>Economy</b>
• /bal — Profile: coins, title, weapon, kills <i>(or reply)</i>
• /daily — Claim <b>1,000</b> coins every 24h
• /weekly — Claim <b>5,000</b> coins every 7 days
• /monthly — Claim <b>10,000</b> coins every 30 days
• /kill — Kill someone for coins <i>(reply)</i>
• /rob — Steal someone's coins <i>(reply)</i>
• /leaderboard — Richest members 🌍/👥
• /topkills — Most kills 🌍/👥

━━━━━━━━━━━━━━━━━━
🏪 <b>Shop</b>  (<code>/shop</code>)
🔫 <b>Weapons</b> — affect /kill success &amp; duel damage
  • Glock 17 (Pistol) — 800 🪙
  • Desert Eagle (Pistol) — 2,500 🪙
  • MP5 (SMG) — 4,000 🪙
  • UZI (SMG) — 5,500 🪙
  • AK-47 (Rifle) — 8,000 🪙
  • M4A1 (Rifle) — 11,000 🪙
  • SCAR-H (Rifle) — 16,000 🪙
🍎 <b>Food</b> — boosts HP in duels
  • Apple +25HP — 250 🪙
  • Chicken +60HP — 600 🪙
  • Steak +120HP — 1,100 🪙
  • Medkit +250HP — 2,000 🪙
👑 <b>Titles</b> — shown in /bal
  • Warrior — 1,500 🪙 · Hunter — 4,000 🪙
  • Assassin — 8,000 🪙 · Savage — 13,000 🪙
  • Gangster — 20,000 🪙 · King — 30,000 🪙
  • Legend — 50,000 🪙 · Elite — 80,000 🪙

━━━━━━━━━━━━━━━━━━
⚔️ <b>Duel</b>  <i>(reply to a user)</i>
• /duel — Free duel
• /duel <code>[amount]</code> — Bet coins on the duel
  ↳ Uses your equipped weapon &amp; food HP bonus
  ↳ Winner gets the bet + a kill counted

━━━━━━━━━━━━━━━━━━
🎮 <b>Games</b>  <i>(costs coins, earn more on win)</i>
• /bet <code>[amount]</code> — Dice roll bet
• /football — Score a goal ⚽ (20🪙 entry)
• /basket — Shoot a hoop 🏀 (20🪙 entry)
• /bowling — Strike the pins 🎳 (20🪙 entry)
• /dart — Hit the bullseye 🎯 (20🪙 entry)
• /slot — Spin to win 🎰 (30🪙 entry)

━━━━━━━━━━━━━━━━━━
🔮 <b>Truth or Dare</b>
• /truth — Random truth question
• /dare — Random dare challenge

━━━━━━━━━━━━━━━━━━
🎭 <b>Mafia Game</b>  <i>(groups only)</i>
• /startgame — Open a game lobby
• /join — Join the lobby
• /flee — Leave the lobby
• /startmafia — Begin the game <i>(host)</i>
• /resend — Resend your secret role to DM
• /players — Show alive / dead list
• /stats — Your win/loss record
• /skip — Force-skip phase <i>(host/admin)</i>
• /endgame — Cancel the game <i>(host/admin)</i>
• /gamerules — Full Mafia rules

━━━━━━━━━━━━━━━━━━
📢 <b>Tag All</b>  <i>(admins only)</i>
• /tagall <code>[message]</code> — Tag every member
• Type <code>@all</code> in a message — same effect

━━━━━━━━━━━━━━━━━━
🔨 <b>Moderation</b>
• /ban · /kick · /tban <code>[time]</code>
• /mute · /unmute · /tmute <code>[time]</code>
• /warn · /unwarn · /warns · /resetwarns
• /purge · /pin · /unpin · /unpinall
• /promote · /demote
• /lock · /unlock · /locks
• /filter · /filters · /stop
• /setrules · /rules · /report

━━━━━━━━━━━━━━━━━━
🎉 <b>Fun</b>
• /love · /crush · /q <i>(quote sticker)</i> · /kang
• /hug · /kiss · /slap · /pat · /cuddle
• /poke · /bite · /punch · /wink · /baka

━━━━━━━━━━━━━━━━━━
🤖 <b>AI Chat</b>
• DM me — always replies
• @mention or reply to me in groups
""".strip()


async def help_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("🔙 Back to Start", callback_data="show_start"),
    ]])
    await update.message.reply_text(HELP_TEXT, parse_mode="HTML", reply_markup=keyboard)


async def help_callback(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    query = update.callback_query
    await query.answer()
    keyboard = InlineKeyboardMarkup([[
        InlineKeyboardButton("🔙 Back to Start", callback_data="show_start"),
    ]])
    await query.message.reply_text(
        text=HELP_TEXT,
        parse_mode="HTML",
        reply_markup=keyboard,
    )
