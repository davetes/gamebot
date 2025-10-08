import os
import sqlite3
from pathlib import Path
from django.conf import settings
from telegram import Update, InlineKeyboardMarkup, InlineKeyboardButton, WebAppInfo
from telegram.ext import ContextTypes

MIN_DEPOSIT_ETB = 50

MIN_BLOCK = (
    f"Here are the min you can deposit\n"
    f"Min Amount:     {MIN_DEPOSIT_ETB} ETB"
)


def _code_block(text: str) -> str:
    # Use <pre> to avoid markdown parsing issues and make it copy friendly
    return f"<pre>{text}</pre>"

DB_FILE = str(Path(settings.BASE_DIR).parent / "usage.db")

def ensure_deposits_table() -> None:
    """Create deposits table if it doesn't exist."""
    conn = sqlite3.connect(DB_FILE)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS deposits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER NOT NULL,
                amount REAL NOT NULL,
                method TEXT NOT NULL,
                reference TEXT,
                status TEXT NOT NULL DEFAULT 'pending',
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                approved_at TIMESTAMP
            )
            """
        )
        conn.commit()
    finally:
        conn.close()

def ensure_admin_txns_table() -> None:
    """Create admin_txns table if it doesn't exist.

    This table stores transaction references provided by admins that can be
    auto-validated when users submit their references from the WebApp.

    Columns:
      - id INTEGER PK
      - method TEXT (e.g., 'cbe', 'boa', 'telebirr', 'cbe-birr')
      - reference TEXT UNIQUE (bank ref / code)
      - amount REAL (optional; can be 0 or NULL)
      - used_by INTEGER (user_id who consumed it)
      - used_at TIMESTAMP
      - notes TEXT (optional admin notes)
    """
    conn = sqlite3.connect(DB_FILE)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            CREATE TABLE IF NOT EXISTS admin_txns (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                method TEXT NOT NULL,
                reference TEXT NOT NULL UNIQUE,
                amount REAL,
                used_by INTEGER,
                used_at TIMESTAMP,
                notes TEXT
            )
            """
        )
        conn.commit()
    finally:
        conn.close()

def _insert_pending_deposit(user_id: int, amount: float, method: str, reference: str | None) -> int:
    conn = sqlite3.connect(DB_FILE)
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT INTO deposits (user_id, amount, method, reference, status)
            VALUES (?, ?, ?, ?, 'pending')
            """,
            (user_id, amount, method, reference or ""),
        )
        conn.commit()
        return int(cur.lastrowid)
    finally:
        conn.close()


async def start_deposit(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Entry point when user taps Make a Deposit."""
    # Send the min deposit block
    if update.callback_query:
        message = update.callback_query.message
    else:
        message = update.message

    if message:
        await message.reply_text(_code_block(MIN_BLOCK), parse_mode="HTML")
        await message.reply_text("Please enter the amount:")
    # Set state to capture the next text message
    context.user_data["awaiting_deposit_amount"] = True
    # Clear any previous state
    context.user_data.pop("awaiting_deposit_reference", None)
    context.user_data.pop("deposit_amount", None)


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages for deposit flow (amount then reference)."""
    # First, capture reference if we're waiting for it
    if context.user_data.get("awaiting_deposit_reference"):
        reference = (update.message.text or "").strip()
        if not reference:
            await update.message.reply_text("Please enter a valid transaction reference")
            return
        amount = context.user_data.get("deposit_amount")
        if not amount:
            # Safety: if amount missing, restart flow
            context.user_data.pop("awaiting_deposit_reference", None)
            await update.message.reply_text("Let's restart deposit. Tap Make a Deposit again.")
            return
        _insert_pending_deposit(update.effective_user.id, float(amount), "manual", reference)
        context.user_data["awaiting_deposit_reference"] = False
        await update.message.reply_text(
            "✅ Thanks! We received your reference. An admin will review and approve shortly."
        )
        return

    if not context.user_data.get("awaiting_deposit_amount"):
        return  # Not in deposit amount step; let other handlers process

    text = (update.message.text or "").strip()
    # Basic numeric validation
    try:
        amount = float(text)
    except ValueError:
        await update.message.reply_text("Please enter a valid number amount, e.g. 50")
        return

    if amount < MIN_DEPOSIT_ETB:
        await update.message.reply_text(
            f"Min deposit amount is {MIN_DEPOSIT_ETB} ETB, Please try again"
        )
        return

    # Amount accepted; clear the awaiting flag
    context.user_data["awaiting_deposit_amount"] = False
    context.user_data["deposit_amount"] = amount

    # Show method selection. If a DEPOSIT_WEBAPP_URL is configured, provide a WebApp button
    url = os.environ.get("DEPOSIT_WEBAPP_URL", "").strip()
    if url.lower().startswith("https://"):
        full = f"{url}?mode=deposit&amount={int(amount) if amount else ''}"
        await update.message.reply_text(
            "Choose Deposit Method",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Manual-Payment", web_app=WebAppInfo(url=full))]]
            ),
        )
    else:
        await update.message.reply_text(
            "Choose Deposit Method",
            reply_markup=InlineKeyboardMarkup(
                [[InlineKeyboardButton("Manual-Payment", callback_data="deposit_manual")]]
            ),
        )


async def handle_deposit_method(update: Update, context: ContextTypes.DEFAULT_TYPE):
    query = update.callback_query
    if query.data != "deposit_manual":
        return
    amount = context.user_data.get("deposit_amount")
    # If a DEPOSIT_WEBAPP_URL is configured, open the mini app to show bank options
    url = os.environ.get("DEPOSIT_WEBAPP_URL", "").strip()
    if url.lower().startswith("https://"):
        full = f"{url}?mode=deposit&amount={int(amount) if amount else ''}"
        await query.message.reply_text(
            "Manual Deposit",
            reply_markup=InlineKeyboardMarkup([
                [InlineKeyboardButton("Open Manual Deposit", web_app=WebAppInfo(url=full))]
            ]),
        )
        return

    # Fallback: plain text instructions and ask for reference
    text = (
        "📥 Manual Payment Selected\n\n"
        f"Amount: {amount} ETB\n\n"
        "Please send the payment to the provided account and reply with the reference number."
    )
    await query.message.reply_text(text)
    await query.message.reply_text("Enter the bank transaction number (e.g. FTxxxx…)")
    # Next text will be the reference
    context.user_data["awaiting_deposit_reference"] = True


def _credit_user_balance(cur: sqlite3.Cursor, user_id: int, amount: float) -> None:
    """Ensure users table has balance and credit it."""
    cur.execute("PRAGMA table_info(users)")
    cols = {c[1] for c in cur.fetchall()}
    if "balance" not in cols:
        cur.execute("ALTER TABLE users ADD COLUMN balance REAL DEFAULT 0")
    cur.execute(
        "UPDATE users SET balance = COALESCE(balance, 0) + ? WHERE user_id = ?",
        (float(amount), int(user_id)),
    )


def _normalize_method(method: str | None) -> str | None:
    if not method:
        return None
    m = method.strip().lower()
    allowed = {"telebirr", "cbe", "boa", "cbe-birr"}
    return m if m in allowed else None


def verify_deposit_reference(user_id: int, method: str, amount: float | None, reference: str) -> tuple[bool, str]:
    """Verify a deposit reference against admin-provided data.

    Returns (ok, message). If ok=True, the deposit is approved and balance credited.
    If ok=False, the reference is recorded as pending for manual review.
    """
    ensure_deposits_table()
    ensure_admin_txns_table()

    ref = (reference or "").strip()
    norm_method = _normalize_method(method)
    if not norm_method:
        return False, "Unsupported payment method."
    if not ref or len(ref) < 8:
        return False, "Invalid transaction reference."

    conn = sqlite3.connect(DB_FILE)
    try:
        cur = conn.cursor()
        # Try to find a matching admin-provided txn that is not used yet
        cur.execute(
            "SELECT id, amount, used_by FROM admin_txns WHERE reference = ? AND method = ?",
            (ref, norm_method),
        )
        row = cur.fetchone()

        if row and row[2] is None:
            admin_id, admin_amount, _ = row
            credit_amount = float(amount) if amount is not None else (float(admin_amount) if admin_amount is not None else 0.0)
            # Insert an approved deposit and credit balance
            cur.execute(
                """
                INSERT INTO deposits (user_id, amount, method, reference, status, approved_at)
                VALUES (?, ?, ?, ?, 'approved', CURRENT_TIMESTAMP)
                """,
                (int(user_id), float(credit_amount), norm_method, ref),
            )
            _credit_user_balance(cur, int(user_id), float(credit_amount))
            # Mark admin txn as used
            cur.execute(
                "UPDATE admin_txns SET used_by = ?, used_at = CURRENT_TIMESTAMP WHERE id = ?",
                (int(user_id), int(admin_id)),
            )
            conn.commit()
            return True, "✅ Transaction verified and balance credited."

        # Not found or already used: record as pending for moderation
        _insert_pending_deposit(int(user_id), float(amount or 0), norm_method, ref)
        conn.commit()
        return False, "✅ Reference submitted. An admin will review shortly."
    finally:
        conn.close()
