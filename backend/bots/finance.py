import sqlite3
import html
from pathlib import Path
from django.conf import settings

# Use the same DB as other modules
DB_FILE = str(Path(settings.BASE_DIR).parent / "usage.db")


def ensure_user_finance_columns():
    """Ensure balance/coin columns exist on the users table."""
    conn = sqlite3.connect(DB_FILE)
    try:
        cur = conn.cursor()
        cur.execute("PRAGMA table_info(users)")
        cols = {row[1] for row in cur.fetchall()}
        if "balance_etb" not in cols:
            cur.execute("ALTER TABLE users ADD COLUMN balance_etb REAL DEFAULT 0.0")
        if "coin" not in cols:
            cur.execute("ALTER TABLE users ADD COLUMN coin REAL DEFAULT 0.10")
        conn.commit()
    finally:
        conn.close()


def get_user_finance(user_id: int) -> tuple[float, float]:
    """Return (balance_etb, coin) for a user, defaulting to (0.0, 0.10)."""
    conn = sqlite3.connect(DB_FILE)
    try:
        cur = conn.cursor()
        cur.execute("SELECT balance_etb, coin FROM users WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        if row and row[0] is not None and row[1] is not None:
            return float(row[0]), float(row[1])
        return 0.0, 0.10
    finally:
        conn.close()


def format_balance_block(username: str, bal: float, coin: float) -> str:
    """Return the multi-line block for balance display using HTML <pre> to avoid Markdown parsing issues."""
    safe_user = html.escape(username or '-')
    body = (
        f"Username:     {safe_user}\n"
        f"Balance:      {bal:.2f} ETB\n"
        f"Coin:         {coin:.2f}"
    )
    return f"<pre>{body}</pre>"


def add_coins(user_id: int, delta: float) -> None:
    """Increment a user's coin balance by delta. Creates the row if missing."""
    conn = sqlite3.connect(DB_FILE)
    try:
        cur = conn.cursor()
        # Ensure user row exists
        cur.execute("SELECT coin FROM users WHERE user_id = ?", (user_id,))
        row = cur.fetchone()
        if row is None:
            cur.execute(
                "INSERT INTO users(user_id, phone, created_at, balance_etb, coin) VALUES(?, NULL, datetime('now'), 0.0, 0.0)",
                (user_id,),
            )
        # Apply increment
        cur.execute("UPDATE users SET coin = COALESCE(coin, 0) + ? WHERE user_id = ?", (float(delta), user_id))
        conn.commit()
    finally:
        conn.close()
