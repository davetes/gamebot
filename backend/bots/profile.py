import sqlite3
from pathlib import Path
from django.conf import settings
from telegram import Update
from telegram.ext import ContextTypes

DB_FILE = str(Path(settings.BASE_DIR).parent / "usage.db")


def ensure_username_column():
    """Add a username column to users table if it doesn't exist."""
    conn = sqlite3.connect(DB_FILE)
    try:
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(users)")
        cols = {row[1] for row in cur.fetchall()}
        if "username" not in cols:
            cur.execute("ALTER TABLE users ADD COLUMN username TEXT")
        conn.commit()
    finally:
        conn.close()


def set_username(user_id: int, username: str) -> None:
    conn = sqlite3.connect(DB_FILE)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            UPDATE users
            SET username = ?
            WHERE user_id = ?
            """,
            (username, user_id),
        )
        conn.commit()
    finally:
        conn.close()


async def prompt_change_username(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Ask the user to send a new username; mark awaiting flag."""
    context.user_data["awaiting_username_change"] = True
    await (update.message or update.callback_query.message).reply_text(
        "Please enter a new username"
    )


async def handle_username_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Capture the next text message when awaiting_username_change is set and save it."""
    if not context.user_data.get("awaiting_username_change"):
        return  # not in username-change flow

    new_username = (update.message.text or "").strip()
    if not new_username:
        await update.message.reply_text("Username cannot be empty. Please enter a new username")
        return

    set_username(update.effective_user.id, new_username)
    context.user_data["awaiting_username_change"] = False
    await update.message.reply_text("Username updated successfully!")
