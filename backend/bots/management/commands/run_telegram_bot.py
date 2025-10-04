import sqlite3
import asyncio
from datetime import datetime
from pathlib import Path
from telegram import BotCommand, Update, InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler, MessageHandler, filters
from telegram.request import HTTPXRequest
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
import os
from bots.registration import (
    ensure_users_table,
    handle_register_command,
    handle_contact,
    build_register_keyboard,
    is_registered,
    send_registration_prompt,
    ensure_referral_column,
    record_referral_if_missing,
)
from bots.finance import (
    ensure_user_finance_columns,
    get_user_finance,
    format_balance_block,
)
from bots.profile import (
    ensure_username_column,
    prompt_change_username,
    handle_username_text,
    get_username,
)
from bots.invite import send_invite

# -----------------------
# Database Setup
# -----------------------
# Store DB at the repository root (same location as original usage.db)
DB_FILE = str(Path(settings.BASE_DIR).parent / "usage.db")

def init_db():
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
    CREATE TABLE IF NOT EXISTS usage (
        user_id INTEGER,
        username TEXT,
        month TEXT,
        PRIMARY KEY(user_id, month)
    )
    """)

    conn.commit()
    conn.close()


def get_monthly_user_count():
    month = datetime.now().strftime("%Y-%m")
    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM usage WHERE month = ?", (month,))
    count = cursor.fetchone()[0]

    conn.close()
    return count


def format_user_count(count):
    """Format the user count with comma separators"""
    return f"{count:,}"


async def log_user_usage(user_id, username):
    month = datetime.now().strftime("%Y-%m")

    conn = sqlite3.connect(DB_FILE)
    cursor = conn.cursor()

    cursor.execute("""
    INSERT OR IGNORE INTO usage (user_id, username, month) VALUES (?, ?, ?)
    """, (user_id, username, month))

    conn.commit()
    conn.close()


# -----------------------
# Command Handlers
# -----------------------
async def start(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await log_user_usage(user.id, user.username or "")

    # Handle deep-link referrals: /start <referrer_id>
    try:
        if context.args and len(context.args) > 0:
            referrer_str = context.args[0].strip()
            if referrer_str.isdigit():
                ref_id = int(referrer_str)
                record_referral_if_missing(user.id, ref_id)
    except Exception as e:
        print(f"Referral parse failed: {e}")

    # First-time gating: prompt registration if not registered (with share-phone keyboard)
    if not is_registered(user.id):
        await send_registration_prompt(update, context, with_keyboard=True)

    webapp_url = os.environ.get("LEADERBOARD_WEBAPP_URL")
    leaderboard_btn = (
        InlineKeyboardButton("🏅 Leaderboard", web_app=WebAppInfo(url=webapp_url))
        if webapp_url else InlineKeyboardButton("🏅 Leaderboard", callback_data="leaderboard")
    )

    keyboard = [
        [InlineKeyboardButton("🎮 Play Now", callback_data="play_now")],
        [
            InlineKeyboardButton("💰 Check Balance", callback_data="check_balance"),
            InlineKeyboardButton("💳 Make a Deposit", callback_data="make_deposit"),
        ],
        [
            InlineKeyboardButton("🆘 Support", callback_data="support"),
            InlineKeyboardButton("📖 Instructions", callback_data="instructions"),
        ],
        [
            InlineKeyboardButton("📤 Invite", callback_data="invite"),
            InlineKeyboardButton("🏆 Win Patterns", callback_data="win_patterns"),
        ],
        [
            InlineKeyboardButton("👤 Change Username", callback_data="change_username"),
            leaderboard_btn,
        ],
    ]

    # Show Register button ONLY for users who are not yet registered, on the SAME row as Play Now
    if not is_registered(user.id):
        keyboard[0].append(InlineKeyboardButton("📱 Register", callback_data="register"))
    reply_markup = InlineKeyboardMarkup(keyboard)

    welcome_text = (
        "*🎉Welcome To luckybot Bingo!🎉* 🌟\n\n"
        "🕹️Every Square Counts – Grab Your lucky, Join the Game, and Let the Fun Begin! 🎯\n\n"
    )

    image_url = "https://www.startpage.com/av/proxy-image?piurl=https%3A%2F%2Fchipy.com%2Fupload%2Ftms%2Feasy.png&sp=1759430612Tbdfbf2a1dec897fd82013f50470f7f659732318d8a14f4080514987a8b9b913e"

    try:
        await update.message.reply_photo(
            photo=image_url,
            caption=welcome_text,
            reply_markup=reply_markup,
            parse_mode='Markdown',
        )
    except Exception as e:
        print(f"Start image failed: {e}")
        await update.message.reply_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode='Markdown',
        )


async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()

    user = query.from_user
    await log_user_usage(user.id, user.username or "")

    # First-time gating for button clicks: allow 'register' and 'invite' before registration
    if query.data not in {"register", "invite"} and not is_registered(user.id):
        await query.message.reply_text("Before you continue, please finish registration. Use /register. Thanks!")
        return

    if query.data == "play_now":
        await query.edit_message_text("🎮 *Starting a new Bingo game...*\n\nGet ready to play!", parse_mode='Markdown')
    elif query.data == "check_balance":
        # Show formatted balance using a code block
        # Prefer custom username stored in DB; fallback to Telegram username
        stored = get_username(query.from_user.id)
        username = stored or (query.from_user.username or "-")
        bal, coin = get_user_finance(query.from_user.id)
        msg = format_balance_block(username, bal, coin)
        await query.message.reply_text(msg, parse_mode='HTML', disable_web_page_preview=True)
    elif query.data == "make_deposit":
        await query.edit_message_text("💳 *Make a Deposit*\n\nUse /deposit to add funds to your account", parse_mode='Markdown')
    elif query.data == "support":
        # Send the same contact info as the /contact command, as a new message
        contact_message = (
            "📞 **Contact Support**\n\n"
            "For any questions or support, please contact:\n\n"
            "👤 **Username:** @nftesk\n"
            "📱 **Phone:** 0934455383\n\n"
            "We're here to help you! 💫"
        )
        await query.message.reply_text(contact_message, parse_mode='Markdown', disable_web_page_preview=True)
    elif query.data == "instructions":
        instructions_text = (
            "እንኮን ወደ እድለኛ ቢንጎ መጡ\n\n"
            "1 ለመጫወት ወደቦቱ ሲገቡ register የሚለውን በመንካት ስልክ ቁጥሮትን ያጋሩ\n\n"
            "2 menu ውስጥ በመግባት deposit fund የሚለውን በመንካት በሚፈልጉት የባንክ አካውንት ገንዘብ ገቢ ያድርጉ \n\n"
            "3 menu ውስጥ በመግባት start play የሚለውን በመንካት መወራረድ የሚፈልጉበትን የብር መጠን ይምረጡ።\n\n\n"
            "1 ወደጨዋታው እድገቡ ከሚመጣሎት 100 የመጫወቻ ቁጥሮች መርጠው accept የሚለውን በመንካት የቀጥሉ\n\n"
            "2 ጨዋታው ለመጀመር የተሰጠውን ጊዜ ሲያልቅ ቁጥሮች መውጣት ይጀምራል\n\n"
            "3 የሚወጡት ቁጥሮች የመረጡት እድለኛ ላይ መኖሩን እያረጋገጡ ያቅልሙ\n\n"
            "4 ያቀለሙት አንድ መስመር ወይንም አራት ጠርዝ ላይ ሲመጣ ቢንጎ በማለት ማሸነፍ የችላሉ\n"
            " —አንድ መስመር ማለት\n"
            "    አንድ ወደጎን ወይንም ወደታች ወይንም ዲያጎናል ሲዘጉ\n"
            " — አራት ጠርዝ ልይ ሲመጣሎት \n\n"
            "5 እነዚህ ማሸነፊያ ቁጥሮች ሳይመጣሎት bingo እሚለውን ከነኩ ከጨዋታው ይባረራሉ\n\n"
            "ማሳሰቢያ\n\n"
            "1 የጨዋታ ማስጀመሪያ ሰከንድ (countdown) ሲያልቅ ያሉት ተጫዋች ብዛት ከ2 በታች ከሆነ ያ ጨዋታ አይጀምርም \n"
            "2 ጨዋታ ከጀመረ በህዋላ እድለኛ መምረጫ ቦርዱ ይፀዳል\n"
            "3 እርሶ በዘጉበት ቁጥር ሌላ ተጫዋች ዘግቶ ቀድሞ bingo ካለ አሸናፊነትዋን ያጣሉ\n\n"
            "📝ስለሆነም እንዚህን ማሳሰቢያዎች ተመልክተው እንዲጠቀሙበት እድለኛ ቢንጎ ያሳስባል"
        )
        # If the original message is a photo (with caption), editing text fails.
        # Send a new message instead of editing the original message.
        await query.message.reply_text(instructions_text, disable_web_page_preview=True)
    elif query.data == "register":
        await query.message.reply_text(
            "Please share your phone number to complete registration.",
            reply_markup=build_register_keyboard(),
        )
    elif query.data == "invite":
        # Send a new message with deep-link instead of editing (editing may fail on media messages)
        await send_invite(update, context)
    elif query.data == "win_patterns":
        win_patterns_text = (
            "🎯 *From straight lines to funky shapes – every pattern is a chance to WIN BIG!*\n\n"
            "Know the pattern, play smart, and shout BINGO when the stars align! ✨"
        )

        try:
            with open("winpattern.jpg", "rb") as photo:
                await query.message.reply_photo(
                    photo=photo,
                    caption=win_patterns_text,
                    parse_mode='Markdown',
                )
        except FileNotFoundError:
            try:
                patterns_image_url = "https://www.startpage.com/av/proxy-image?piurl=https%3A%2F%2Fchipy.com%2Fupload%2Ftms%2Feasy.png&sp=1759430612Tbdfbf2a1dec897fd82013f50470f7f659732318d8a14f4080514987a8b9b913e"
                await query.message.reply_photo(
                    photo=patterns_image_url,
                    caption=win_patterns_text,
                    parse_mode='Markdown',
                )
            except Exception as e:
                print(f"Win patterns image failed: {e}")
                await query.message.reply_text(
                    f"🏆 *Win Patterns*\n\n{win_patterns_text}",
                    parse_mode='Markdown',
                )
        except Exception as e:
            print(f"Win patterns error: {e}")
            await query.message.reply_text(
                f"🏆 *Win Patterns*\n\n{win_patterns_text}",
                parse_mode='Markdown',
            )
    elif query.data == "change_username":
        # Start username change flow (handled in profile.py)
        await prompt_change_username(update, context)
    elif query.data == "leaderboard":
        # Open Telegram Mini App (WebApp) for the leaderboard
        webapp_url = os.environ.get("LEADERBOARD_WEBAPP_URL")
        if not webapp_url:
            await query.message.reply_text(
                "Leaderboard is not configured. Set LEADERBOARD_WEBAPP_URL in your environment.")
        else:
            await query.message.reply_text(
                "🏅 Leaderboard",
                reply_markup=InlineKeyboardMarkup([
                    [InlineKeyboardButton("Open Leaderboard", web_app=WebAppInfo(url=webapp_url))]
                ]),
            )


async def play(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await log_user_usage(user.id, user.username or "")
    if not is_registered(user.id):
        await send_registration_prompt(update, context, with_keyboard=True)
        return
    await update.message.reply_text("🎮 Starting a new Bingo game...")


async def balance(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Reply with the user's balance in the requested copied-code style."""
    user = update.effective_user
    await log_user_usage(user.id, user.username or "")
    if not is_registered(user.id):
        await send_registration_prompt(update, context, with_keyboard=True)
        return
    bal, coin = get_user_finance(user.id)
    stored = get_username(user.id)
    username = stored or (user.username or "-")
    msg = format_balance_block(username, bal, coin)
    await update.message.reply_text(msg, parse_mode='HTML', disable_web_page_preview=True)


async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await log_user_usage(user.id, user.username or "")
    if not is_registered(user.id):
        await send_registration_prompt(update, context, with_keyboard=True)
        return

    contact_message = (
        "📞 **Contact Support**\n\n"
        "For any questions or support, please contact:\n\n"
        "👤 **Username:** @nftesk\n"
        "📱 **Phone:** 0934455383\n\n"
        "We're here to help you! 💫"
    )

    await update.message.reply_text(contact_message)


async def set_commands(application: Application):
    commands = [
        BotCommand("start", "Start the bot"),
        BotCommand("play", "Start playing"),
        BotCommand("transfer", "To transfer funds"),
        BotCommand("withdraw", "To withdraw"),
        BotCommand("balance", "Check balance"),
        BotCommand("deposit", "Deposit funds"),
        BotCommand("language", "Choose language"),
        BotCommand("convert", "Convert coins to wallet"),
        BotCommand("transactions", "Transaction history"),
        BotCommand("game", "Game history"),
        BotCommand("instruction", "Game instruction"),
        BotCommand("invite", "Invite friends"),
        BotCommand("contact", "Contact support"),
    ]

    try:
        await application.bot.set_my_commands(commands)
        print("✅ Bot commands set successfully")
    except Exception as e:
        print(f"❌ Failed to set commands: {e}")


async def update_bio_once(application: Application):
    user_count = get_monthly_user_count()
    formatted_count = format_user_count(user_count)
    bio_text = f"{formatted_count} monthly users"

    try:
        await application.bot.set_my_short_description(bio_text)
        print(f"✅ Updated bot bio: {bio_text}")
    except Exception as e:
        print(f"❌ Failed to update bot bio: {e}")


class Command(BaseCommand):
    help = "Run the Telegram bot"

    def handle(self, *args, **options):
        init_db()
        ensure_users_table()
        ensure_user_finance_columns()
        ensure_username_column()
        ensure_referral_column()

        # Read token from environment (.env is loaded by Django settings)
        token = os.environ.get("TELEGRAM_BOT_TOKEN")
        if not token:
            raise CommandError("TELEGRAM_BOT_TOKEN is not set. Add it to your .env at the repository root.")

        # Optional network configuration from .env
        connect_timeout = float(os.environ.get("TELEGRAM_HTTP_CONNECT_TIMEOUT", 10))
        read_timeout = float(os.environ.get("TELEGRAM_HTTP_READ_TIMEOUT", 30))

        # Note: python-telegram-bot==20.3 HTTPXRequest does not accept a 'proxy' kwarg.
        # If you need a proxy, set environment variables HTTPS_PROXY/HTTP_PROXY instead.
        request = HTTPXRequest(
            connect_timeout=connect_timeout,
            read_timeout=read_timeout,
        )

        app = (
            Application.builder()
            .token(token)
            .request(request)
            .build()
        )

        app.add_handler(CommandHandler("start", start))
        app.add_handler(CommandHandler("play", play))
        app.add_handler(CommandHandler("balance", balance))
        app.add_handler(CommandHandler("register", handle_register_command))
        app.add_handler(CommandHandler("invite", send_invite))
        app.add_handler(CommandHandler("contact", contact))
        app.add_handler(CallbackQueryHandler(button_handler))
        app.add_handler(MessageHandler(filters.CONTACT, handle_contact))
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_username_text))

        async def on_startup(app_instance):
            try:
                await set_commands(app_instance)
                await update_bio_once(app_instance)
            except Exception as e:
                print(f"❌ Startup setup failed: {e}")
            print("✅ Bot setup completed")

        app.post_init = on_startup

        print("🤖 Bot is starting (via Django management command)...")

        try:
            app.run_polling(
                poll_interval=1.0,
                timeout=10,
                drop_pending_updates=True,
                allowed_updates=Update.ALL_TYPES,
            )
        except KeyboardInterrupt:
            print("\n🛑 Bot stopped by user")
        except Exception as e:
            print(f"❌ Bot error: {e}")
            print("💡 This might be a temporary network issue. Try again.")
