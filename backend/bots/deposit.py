import os
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


async def handle_text(update: Update, context: ContextTypes.DEFAULT_TYPE):
    """Handle text messages when awaiting deposit amount."""
    if not context.user_data.get("awaiting_deposit_amount"):
        return  # Not in deposit flow; let other handlers process

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

    # Show method selection
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

    # Fallback: plain text instructions
    text = (
        "📥 Manual Payment Selected\n\n"
        f"Amount: {amount} ETB\n\n"
        "Please send the payment to the provided account and reply with the reference number."
    )
    await query.message.reply_text(text)
