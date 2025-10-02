import sqlite3
import asyncio
from datetime import datetime
from telegram import BotCommand, Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, ContextTypes, CallbackQueryHandler

# -----------------------
# Database Setup
# -----------------------
DB_FILE = "usage.db"

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
    
    # Create inline keyboard buttons
    keyboard = [
        [
            InlineKeyboardButton("🎮 Play Now", callback_data="play_now"),
        ],
        [
            InlineKeyboardButton("💰 Check Balance", callback_data="check_balance"),
            InlineKeyboardButton("💳 Make a Deposit", callback_data="make_deposit")
        ],
        [
            InlineKeyboardButton("🆘 Support", callback_data="support"),
            InlineKeyboardButton("📖 Instructions", callback_data="instructions")
        ],
        [
            InlineKeyboardButton("📤 Invite", callback_data="invite"),
            InlineKeyboardButton("🏆 Win Patterns", callback_data="win_patterns"),
        ],
        [
            InlineKeyboardButton("👤 Change Username", callback_data="change_username"),
            InlineKeyboardButton("🏅 Leaderboard", callback_data="leaderboard")
        ]
    ]
    reply_markup = InlineKeyboardMarkup(keyboard)
    
    # Welcome message
    welcome_text = (
        "*🎉Welcome To luckybot Bingo!🎉* 🌟\n\n"
        "🕹️Every Square Counts – Grab Your lucky, Join the Game, and Let the Fun Begin! 🎯\n\n"
    )
    
    # Use a simpler, more reliable image URL
    image_url = "https://www.startpage.com/av/proxy-image?piurl=https%3A%2F%2Fchipy.com%2Fupload%2Ftms%2Feasy.png&sp=1759430612Tbdfbf2a1dec897fd82013f50470f7f659732318d8a14f4080514987a8b9b913e"
    
    try:
        await update.message.reply_photo(
            photo=image_url,
            caption=welcome_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )
    except Exception as e:
        print(f"Start image failed: {e}")
        # Fallback to text only
        await update.message.reply_text(
            welcome_text,
            reply_markup=reply_markup,
            parse_mode='Markdown'
        )

async def button_handler(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    await query.answer()
    
    user = query.from_user
    await log_user_usage(user.id, user.username or "")
    
    # Handle different button clicks
    if query.data == "play_now":
        await query.edit_message_text("🎮 *Starting a new Bingo game...*\n\nGet ready to play!", parse_mode='Markdown')
    elif query.data == "check_balance":
        await query.edit_message_text("💰 *Check Balance*\n\nYour current balance: 0 coins", parse_mode='Markdown')
    elif query.data == "make_deposit":
        await query.edit_message_text("💳 *Make a Deposit*\n\nUse /deposit to add funds to your account", parse_mode='Markdown')
    elif query.data == "support":
        await query.edit_message_text("🆘 *Support*\n\nFor assistance, contact @nftesk or call 0934455383", parse_mode='Markdown')
    elif query.data == "instructions":
        await query.edit_message_text("📖 *Instructions*\n\nUse /instruction to see game rules", parse_mode='Markdown')
    elif query.data == "invite":
        await query.edit_message_text("📤 *Invite Friends*\n\nUse /invite to share with friends", parse_mode='Markdown')
    elif query.data == "win_patterns":
        win_patterns_text = (
            "🎯 *From straight lines to funky shapes – every pattern is a chance to WIN BIG!*\n\n"
            "Know the pattern, play smart, and shout BINGO when the stars align! ✨"
        )
        
        try:
            # Try to use local file first
            with open("winpattern.jpg", "rb") as photo:
                await query.message.reply_photo(
                    photo=photo,
                    caption=win_patterns_text,
                    parse_mode='Markdown'
                )
        except FileNotFoundError:
            # Fallback to URL image
            try:
                patterns_image_url = "https://www.startpage.com/av/proxy-image?piurl=https%3A%2F%2Fchipy.com%2Fupload%2Ftms%2Feasy.png&sp=1759430612Tbdfbf2a1dec897fd82013f50470f7f659732318d8a14f4080514987a8b9b913e"
                await query.message.reply_photo(
                    photo=patterns_image_url,
                    caption=win_patterns_text,
                    parse_mode='Markdown'
                )
            except Exception as e:
                print(f"Win patterns image failed: {e}")
                await query.message.reply_text(
                    f"🏆 *Win Patterns*\n\n{win_patterns_text}",
                    parse_mode='Markdown'
                )
        except Exception as e:
            print(f"Win patterns error: {e}")
            await query.message.reply_text(
                f"🏆 *Win Patterns*\n\n{win_patterns_text}",
                parse_mode='Markdown'
            )
    elif query.data == "change_username":
        await query.edit_message_text("👤 *Change Username*\n\nContact support to change your username", parse_mode='Markdown')
    elif query.data == "leaderboard":
        await query.edit_message_text("🏅 *Leaderboard*\n\nCheck the top players ranking", parse_mode='Markdown')

async def play(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await log_user_usage(user.id, user.username or "")
    await update.message.reply_text("🎮 Starting a new Bingo game...")

async def contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    user = update.effective_user
    await log_user_usage(user.id, user.username or "")
    
    contact_message = (
        "📞 **Contact Support**\n\n"
        "For any questions or support, please contact:\n\n"
        "👤 **Username:** @nftesk\n"
        "📱 **Phone:** 0934455383\n\n"
        "We're here to help you! 💫"
    )
    
    await update.message.reply_text(contact_message)

# -----------------------
# Update Bot Menu (Simplified - No retry logic)
# -----------------------
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

# -----------------------
# Update Bio (Simplified)
# -----------------------
async def update_bio_once(application: Application):
    user_count = get_monthly_user_count()
    formatted_count = format_user_count(user_count)
    bio_text = f"{formatted_count} monthly users"
    
    try:
        await application.bot.set_my_short_description(bio_text)
        print(f"✅ Updated bot bio: {bio_text}")
    except Exception as e:
        print(f"❌ Failed to update bot bio: {e}")

# -----------------------
# Main - ULTRA SIMPLIFIED AND STABLE
# -----------------------
def main():
    init_db()

    # Create application with better timeout settings
    app = Application.builder().token("8165919801:AAFF34XoxSsMYmIv2uCGGUgW30G9ieqciNU").build()

    app.add_handler(CommandHandler("start", start))
    app.add_handler(CommandHandler("play", play))
    app.add_handler(CommandHandler("contact", contact))
    app.add_handler(CallbackQueryHandler(button_handler))

    async def on_startup(app):
        # Do initial setup once, then stop
        try:
            await set_commands(app)
            await update_bio_once(app)
        except Exception as e:
            print(f"❌ Startup setup failed: {e}")
        print("✅ Bot setup completed")

    app.post_init = on_startup

    print("🤖 Bot is starting...")
    
    # Simple run with better error handling
    try:
        app.run_polling(
            poll_interval=1.0,
            timeout=10,
            drop_pending_updates=True,
            allowed_updates=Update.ALL_TYPES
        )
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Bot error: {e}")
        print("💡 This might be a temporary network issue. Try again.")

if __name__ == "__main__":
    main()