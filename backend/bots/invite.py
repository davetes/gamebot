from telegram import InlineKeyboardButton, InlineKeyboardMarkup, Update
from telegram.ext import ContextTypes
from urllib.parse import quote_plus


async def send_invite(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Send an invite message with a deep-link to the bot that includes the user's referral code."""
    user = update.effective_user
    # Get bot username to build t.me deep link
    me = await context.bot.get_me()
    bot_username = (me.username or "").lstrip("@")

    # Build deep links (both https and tg scheme) to maximize client compatibility
    payload = quote_plus(str(user.id))
    https_link = f"https://t.me/{bot_username}?start={payload}" if bot_username else None
    tg_link = f"tg://resolve?domain={bot_username}&start={payload}" if bot_username else None

    if bot_username:
        link_line = f"Link: {https_link}"
    else:
        link_line = (
            "Link could not be built because the bot has no username.\n"
            "Ask BotFather to set a username for your bot, then try again."
        )

    text = (
        "🎉 Invite friends to luckybet Bingo!\n\n"
        "Share your personal link below. When your friends join, they start right away.\n\n"
        f"{link_line}"
    )

    keyboard_rows = []
    if https_link:
        keyboard_rows.append([InlineKeyboardButton("📨 Open in Telegram", url=https_link)])
    if tg_link:
        keyboard_rows.append([InlineKeyboardButton("📱 Open App (tg://)", url=tg_link)])
    keyboard = keyboard_rows or [[InlineKeyboardButton("Help: Set bot username in BotFather", url="https://t.me/BotFather")]]

    # Send either as a reply to a message or to a callback query's message
    if update.message:
        await update.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), disable_web_page_preview=True)
    elif update.callback_query and update.callback_query.message:
        await update.callback_query.message.reply_text(text, reply_markup=InlineKeyboardMarkup(keyboard), disable_web_page_preview=True)
