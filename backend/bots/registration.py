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


def build_register_keyboard() -> ReplyKeyboardMarkup:
    kb = [[KeyboardButton(text="📲 Share phone", request_contact=True)]]
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
    conn = sqlite3.connect(DB_FILE)
    try:
        cur = conn.cursor()
        cur.execute("SELECT 1 FROM users WHERE user_id = ? LIMIT 1", (user_id,))
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
