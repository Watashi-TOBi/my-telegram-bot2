import random
from telegram import Update
from telegram.ext import ContextTypes

_TRUTHS = [
    "What's the most embarrassing thing you've ever done in public?",
    "What's a secret you've never told anyone in this chat?",
    "Have you ever lied to get out of trouble? What was the lie?",
    "What's the weirdest dream you've ever had?",
    "Who in this group do you find the most annoying and why?",
    "Have you ever stalked someone's social media? Who?",
    "What's the biggest mistake you've made in a relationship?",
    "Have you ever cheated on a test or game?",
    "What's something you've done that you're not proud of?",
    "Who was your first crush and what happened?",
    "What's the most childish thing you still do?",
    "Have you ever ghosted someone? Why?",
    "What's the pettiest reason you've ever ended or avoided a friendship?",
    "What's something you pretend to like but actually hate?",
    "What's the most money you've ever wasted on something dumb?",
    "Have you ever sent a text to the wrong person? What did it say?",
    "What's your most embarrassing nickname?",
    "Do you have a secret talent you've never shown anyone?",
    "What's the most ridiculous thing you've ever cried about?",
    "Have you ever had a crush on a friend's partner?",
    "What's the longest you've gone without showering?",
    "What's the worst thing you've ever said about someone behind their back?",
    "Have you ever pretended to be sick to avoid something?",
    "What's one thing you'd do if no one was watching?",
    "What's the most embarrassing song on your playlist?",
    "Have you ever walked into a glass door or wall?",
    "What's your most irrational fear?",
    "Have you ever faked laughing at a joke you didn't get?",
    "What's something you Google way too often?",
    "Who in this group would you call at 3 AM with a problem?",
]

_DARES = [
    "Send a voice message saying 'I love potatoes' in the most dramatic way possible.",
    "Change your profile picture to a potato for 10 minutes.",
    "Type a message using only your nose.",
    "Send the 5th photo in your gallery right now — no explanations.",
    "Write a love poem for the person who last messaged you.",
    "Text your mom 'I swallowed a spider' and screenshot her reply.",
    "Do your best impression of a Telegram notification sound.",
    "Write a 2-sentence horror story about this group chat.",
    "Send a voice message speaking in slow motion for 30 seconds.",
    "Compliment every person in this chat in one message.",
    "Change your username to 'Embarrassing Potato' for 5 minutes.",
    "Send a text saying 'I have something to confess...' to a random contact and don't reply for 10 minutes.",
    "Sing the chorus of a song you hate and send it as a voice message.",
    "Describe your day as if you were a dramatic news reporter.",
    "Send the first meme or sticker in your collection right now.",
    "Write a haiku about your current mood.",
    "Type everything in reverse for the next 3 messages.",
    "Send an embarrassing autocorrect fail story.",
    "Do a TikTok-style intro about yourself and send a voice message.",
    "Admit the last thing you searched on Google.",
    "Say 3 nice things about the person who gave you this dare.",
    "Describe the person to your left using only food emojis.",
    "Send a voice message reciting the alphabet backwards.",
    "Tell an unfunny joke and then laugh at it yourself.",
    "Send a voice message in an accent of someone's choice.",
    "Reply to the next 5 messages with only movie quotes.",
    "Write a product review for this group chat.",
    "Type a message with your eyes closed.",
    "Pretend to be a news anchor and announce today's date dramatically.",
    "Confess the last lie you told someone in this chat.",
]


async def truth_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user     = update.effective_user
    question = random.choice(_TRUTHS)
    await update.message.reply_text(
        f"🔮 <b>Truth for {user.first_name}:</b>\n\n"
        f"<i>{question}</i>",
        parse_mode="HTML",
    )


async def dare_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    dare = random.choice(_DARES)
    await update.message.reply_text(
        f"🔥 <b>Dare for {user.first_name}:</b>\n\n"
        f"<i>{dare}</i>",
        parse_mode="HTML",
    )
