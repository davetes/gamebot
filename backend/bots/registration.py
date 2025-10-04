import sqlite3
from datetime import datetime
from pathlib import Path
from django.conf import settings
from telegram import (
    ReplyKeyboardMarkup,
    KeyboardButton,
    ReplyKeyboardRemove,
    Update,
    InlineKeyboardButton,
    InlineKeyboardMarkup,
)
from telegram.ext import ContextTypes
from bots.finance import add_coins

# Use the same DB location as the bot command
DB_FILE = str(Path(settings.BASE_DIR).parent / "usage.db")


def ensure_users_table():
    conn = sqlite3.connect(DB_FILE)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                user_id INTEGER PRIMARY KEY,
                phone TEXT,
                created_at TEXT
            )
            """
        )
        conn.commit()
    finally:
        conn.close()


def ensure_referral_column():
    """Ensure the users table has a referred_by column."""
    conn = sqlite3.connect(DB_FILE)
    try:
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(users)")
        cols = {row[1] for row in cur.fetchall()}
        if "referred_by" not in cols:
            cur.execute("ALTER TABLE users ADD COLUMN referred_by INTEGER")
        conn.commit()
    finally:
        conn.close()


def record_referral_if_missing(user_id: int, referrer_id: int):
    """Insert user row if missing and set referred_by only if not already set and not self-referral."""
    if referrer_id == user_id:
        return
    conn = sqlite3.connect(DB_FILE)
    try:
        cur = conn.cursor()
        # Ensure row exists
        cur.execute("SELECT referred_by FROM users WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        if row is None:
            cur.execute(
                "INSERT INTO users(user_id, phone, created_at, referred_by) VALUES(?, NULL, ?, ?)",
                (user_id, datetime.utcnow().isoformat(), referrer_id),
            )
        else:
            current_ref = row[0]
            if current_ref is None:
                cur.execute(
                    "UPDATE users SET referred_by = ? WHERE user_id = ? AND referred_by IS NULL",
                    (referrer_id, user_id),
                )
        conn.commit()
    finally:
        conn.close()


def build_register_keyboard() -> ReplyKeyboardMarkup:
    kb = [[
        KeyboardButton(text="📲 Share Phone Number", request_contact=True),
        KeyboardButton(text="Cancel"),
    ]]
    return ReplyKeyboardMarkup(kb, resize_keyboard=True, one_time_keyboard=True)


async def handle_register_command(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Prompt the user to share phone number via a keyboard button."""
    await update.message.reply_text(
        "Please share your phone number to complete registration.",
        reply_markup=build_register_keyboard(),
    )


async def handle_contact(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Save the shared contact phone and confirm registration."""
    if not update.message or not update.message.contact:
        return

    user = update.effective_user
    phone = update.message.contact.phone_number

    conn = sqlite3.connect(DB_FILE)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO users (user_id, phone, created_at)
            VALUES (?, ?, ?)
            ON CONFLICT(user_id) DO UPDATE SET phone=excluded.phone
            """,
            (user.id, phone, datetime.utcnow().isoformat()),
        )
        conn.commit()
    finally:
        conn.close()

    await update.message.reply_text(
        "✅ Registration completed. Thank you!",
        reply_markup=ReplyKeyboardRemove(),
    )

    # Clear any lingering register flow state if present
    context.user_data.pop("awaiting_registration", None)

    # Referral bonus: if this user was referred, add coins to inviter
    try:
        conn = sqlite3.connect(DB_FILE)
        cur = conn.cursor()
        cur.execute("SELECT referred_by FROM users WHERE user_id = ?", (user.id,))
        row = cur.fetchone()
        inviter_id = row[0] if row else None
        conn.close()
        if inviter_id:
            add_coins(inviter_id, 10.0)
    except Exception as e:
        # Soft-fail: do not block registration completion
        print(f"Referral bonus failed: {e}")

    # After successful registration, present the main menu WITHOUT the Register button
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
            InlineKeyboardButton("🏅 Leaderboard", callback_data="leaderboard"),
        ],
    ]

    await update.message.reply_text(
        "You're all set! Explore the menu below.",
        reply_markup=InlineKeyboardMarkup(keyboard),
    )


"""
Financial helpers moved to bots/finance.py (ensure_user_finance_columns, get_user_finance, format_balance_block)
"""


def is_registered(user_id: int) -> bool:
    """A user is considered registered only if we have a non-empty phone stored."""
    conn = sqlite3.connect(DB_FILE)
    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT 1 FROM users WHERE user_id = ? AND phone IS NOT NULL AND TRIM(phone) <> '' LIMIT 1",
            (user_id,),
        )
        return cur.fetchone() is not None
    finally:
        conn.close()


async def send_registration_prompt(update: Update, context: ContextTypes.DEFAULT_TYPE, with_keyboard: bool = False):
    text = "Before you continue, please finish registration. Use /register. Thanks!"
    if with_keyboard:
        await update.message.reply_text(text, reply_markup=build_register_keyboard())
    else:
        # Fallback if no message present (e.g., callback query without message context)
        if update.message:
            await update.message.reply_text(text)
        elif update.callback_query and update.callback_query.message:
            await update.callback_query.message.reply_text(text)


async def handle_register_cancel(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle the Cancel button during registration: remove keyboard and remind user of /register."""
    if update.message and update.message.text.strip().lower() == "cancel":
        await update.message.reply_text(
            "Registration canceled. You can register anytime with /register.",
            reply_markup=ReplyKeyboardRemove(),
        )
        # Keep gating in effect by not marking them registered.
