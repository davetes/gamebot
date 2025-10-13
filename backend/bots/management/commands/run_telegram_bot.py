import sqlite3
import json
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
    handle_register_cancel,
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
from bots.playnow import build_stake_selection, parse_bet_amount
from bots.deposit import (
    start_deposit,
    handle_text as handle_deposit_text,
    handle_deposit_method,
    ensure_deposits_table,
    ensure_admin_txns_table,
    verify_deposit_reference,
)

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


def _clean_webapp_url() -> str | None:
    """Read LEADERBOARD_WEBAPP_URL, trim spaces, and ensure it's https://.
    Returns None if invalid.
    """
    raw = os.environ.get("LEADERBOARD_WEBAPP_URL")
    if not raw:
        return None
    url = raw.strip()
    # Telegram requires HTTPS for WebApp URLs
    if not url.lower().startswith("https://"):
        return None
    return url


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

    webapp_url = _clean_webapp_url()
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
        # Show stake selection like the screenshot
        stake_text, stake_markup = build_stake_selection()
        # Send a new message (editing may fail if previous message is media)
        await query.message.reply_text(stake_text, reply_markup=stake_markup)
    elif query.data == "check_balance":
        # Show formatted balance using a code block
        # Prefer custom username stored in DB; fallback to Telegram username
        stored = get_username(query.from_user.id)
        username = stored or (query.from_user.username or "-")
        bal, coin = get_user_finance(query.from_user.id)
        msg = format_balance_block(username, bal, coin)
        await query.message.reply_text(msg, parse_mode='HTML', disable_web_page_preview=True)
    elif query.data == "make_deposit":
        # Start guided deposit flow (min amount block -> ask amount -> method selection)
        await start_deposit(update, context)
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
    elif query.data == "deposit_manual":
        # User chose manual payment method in the deposit flow
        await handle_deposit_method(update, context)
    elif query.data == "change_username":
        # Start username change flow (handled in profile.py)
        await prompt_change_username(update, context)
    elif query.data == "leaderboard":
        # Open Telegram Mini App (WebApp) for the leaderboard
        webapp_url = _clean_webapp_url()
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
    elif query.data.startswith("bet_"):
        amount = parse_bet_amount(query.data)
        if amount is None:
            await query.message.reply_text("Invalid bet selection.")
        else:
            await query.message.reply_text(
                f"🎮 You selected {amount} ETB stake. Preparing your game…"
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


async def deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Start the same guided deposit flow as the Make a Deposit button."""
    user = update.effective_user
    await log_user_usage(user.id, user.username or "")
    if not is_registered(user.id):
        await send_registration_prompt(update, context, with_keyboard=True)
        return
    await start_deposit(update, context)


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
        ensure_deposits_table()
        ensure_admin_txns_table()

        # Read token from environment (.env is loaded by Django settings)
        token = os.environ.get("TELEGRAM_BOT_TOKEN")
        if not token:
            raise CommandError("TELEGRAM_BOT_TOKEN is not set. Add it to your .env at the repository root.")

        # Optional network configuration from .env (use higher defaults for slow networks)
        connect_timeout = float(os.environ.get("TELEGRAM_HTTP_CONNECT_TIMEOUT", 30))
        read_timeout = float(os.environ.get("TELEGRAM_HTTP_READ_TIMEOUT", 90))

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
        app.add_handler(CommandHandler("deposit", deposit))
        app.add_handler(CommandHandler("register", handle_register_command))
        app.add_handler(CommandHandler("invite", send_invite))
        app.add_handler(CommandHandler("contact", contact))
        app.add_handler(CallbackQueryHandler(button_handler))
        app.add_handler(MessageHandler(filters.CONTACT, handle_contact))
        # Register Cancel handler BEFORE the generic text handler (case-insensitive)
        app.add_handler(MessageHandler(filters.TEXT & filters.Regex("(?i)^cancel$"), handle_register_cancel))
        # Handle WebApp data events from the Mini App (Verify button)
        async def handle_webapp_data(update: Update, context: ContextTypes.DEFAULT_TYPE):
            msg = update.effective_message or update.message
            if not msg:
                print("[WEBAPP] No message found on update")
                return
            wad = getattr(msg, "web_app_data", None)
            if not wad:
                # Not a WebApp data message; ignore silently
                return
            print(f"[WEBAPP] Received web_app_data: {wad.data!r}")
            try:
                data = json.loads(wad.data or "{}")
            except Exception as e:
                print(f"[WEBAPP] JSON parse error: {e}")
                try:
                    await msg.reply_text("Invalid data from Mini App.")
                except Exception as e2:
                    print(f"[WEBAPP] Reply failed: {e2}")
                return

            if data.get("type") == "verify_deposit":
                method = data.get("method")
                amount = None
                if str(data.get("amount") or "").strip():
                    try:
                        amount = float(str(data.get("amount")).replace(",", "").strip())
                    except Exception:
                        amount = None
                reference = data.get("ref") or data.get("reference") or ""
                ok, message = verify_deposit_reference(update.effective_user.id, method, amount, reference)
                try:
                    await msg.reply_text(message)
                except Exception as e2:
                    print(f"[WEBAPP] Reply send failed: {e2}")
            elif data.get("type") == "notify_support":
                # Forward a deposit notification to support and request a screenshot upload next
                method = str(data.get("method") or "-")
                amount_raw = str(data.get("amount") or "-")
                amount_str = amount_raw
                user = update.effective_user

                # Lookup user's stored phone from registration DB
                phone = None
                try:
                    conn = sqlite3.connect(DB_FILE)
                    cur = conn.cursor()
                    cur.execute("SELECT phone FROM users WHERE user_id = ?", (user.id,))
                    row = cur.fetchone()
                    phone = row[0] if row else None
                except Exception as e:
                    print(f"[WEBAPP] phone lookup failed: {e}")
                finally:
                    try:
                        conn.close()
                    except Exception:
                        pass

                support_target = os.environ.get("SUPPORT_TARGET", "@Afamedawa")

                info_block = (
                    "Deposit notification\n"
                    f"Method: {method}\n"
                    f"Amount: {amount_str} ETB\n"
                    f"From: {user.full_name} (@{user.username or '-'}, id:{user.id})\n"
                    f"Phone: {phone or '-'}\n"
                    "Receipt: user will send a screenshot next."
                )

                # Try notifying support chat/channel immediately
                try:
                    await context.bot.send_message(chat_id=support_target, text=info_block)
                except Exception as e:
                    print(f"[WEBAPP] notify support failed: {e}")

                # Mark that we are awaiting a receipt photo from this user
                context.user_data["awaiting_receipt"] = {
                    "method": method,
                    "amount": amount_str,
                    "phone": phone,
                    "support_target": support_target,
                }

                try:
                    await msg.reply_text("Your message was sent successfully. Please send your receipt screenshot now.")
                except Exception as e2:
                    print(f"[WEBAPP] Reply send failed: {e2}")
            else:
                print(f"[WEBAPP] Unhandled type: {data.get('type')} ")
                return

        # Register handler for WebApp data (PTB v20):
        try:
            app.add_handler(MessageHandler(filters.StatusUpdate.WEB_APP_DATA, handle_webapp_data))
        except Exception:
            # Fallback: register with a generic message filter and self-guard in the handler
            app.add_handler(MessageHandler(filters.ALL, handle_webapp_data))
        
        # When the user sends a photo after notify_support, forward it to support with context
        async def handle_user_photo(update: Update, context: ContextTypes.DEFAULT_TYPE):
            user = update.effective_user
            data = context.user_data.get("awaiting_receipt")
            if not data:
                # Not expecting a receipt; ignore graceful
                return
            support_target = data.get("support_target") or os.environ.get("SUPPORT_TARGET", "@Afamedawa")
            method = data.get("method") or "-"
            amount_str = data.get("amount") or "-"
            phone = data.get("phone") or "-"

            caption = (
                "Deposit receipt\n"
                f"Method: {method}\n"
                f"Amount: {amount_str} ETB\n"
                f"From: {user.full_name} (@{user.username or '-'}, id:{user.id})\n"
                f"Phone: {phone}"
            )

            try:
                await context.bot.copy_message(
                    chat_id=support_target,
                    from_chat_id=update.effective_chat.id,
                    message_id=update.message.message_id,
                    caption=caption,
                )
                await update.message.reply_text("Thanks! Your screenshot has been forwarded to support. We will review and credit you shortly.")
                # Clear awaiting flag
                context.user_data.pop("awaiting_receipt", None)
            except Exception as e:
                print(f"[PHOTO] forward failed: {e}")
                try:
                    await update.message.reply_text("Failed to forward screenshot to support. Please try again later.")
                except Exception:
                    pass

        app.add_handler(MessageHandler(filters.PHOTO, handle_user_photo))
        # Deposit handlers first (amount then reference), before generic username handler
        app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, handle_deposit_text))
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
                timeout=30,
                drop_pending_updates=True,
                allowed_updates=Update.ALL_TYPES,
            )
        except KeyboardInterrupt:
            print("\n🛑 Bot stopped by user")
        except Exception as e:
            print(f"❌ Bot error: {e}")
            print("💡 This might be a temporary network issue. Try again.")
