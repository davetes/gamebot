import os
from telegram import InlineKeyboardButton, InlineKeyboardMarkup, WebAppInfo


def _clean_webapp_url() -> str | None:
    """Read LEADERBOARD_WEBAPP_URL from env, ensure it starts with https://, else None."""
    raw = os.environ.get("LEADERBOARD_WEBAPP_URL")
    if not raw:
        return None
    url = raw.strip()
    if not url.lower().startswith("https://"):
        return None
    return url


def build_stake_selection() -> tuple[str, InlineKeyboardMarkup]:
    """Return the text and inline keyboard for the Play Now stake chooser.

    Buttons:
    - 🎮 10 ETB -> callback_data="bet_10"
    - 🎮 20 ETB -> callback_data="bet_20"
    - 🎮 50 ETB -> callback_data="bet_50"
    - 🏆 Leaderboard -> callback_data="leaderboard"
    """
    text = (
        "💰 Choose Your Stake, Play Your Luck – The Bigger the Bet, The Bigger the Glory!"
    )
    webapp_url = _clean_webapp_url()
    leaderboard_btn = (
        InlineKeyboardButton("🏆 Leaderboard", web_app=WebAppInfo(url=webapp_url))
        if webapp_url else InlineKeyboardButton("🏆 Leaderboard", callback_data="leaderboard")
    )

    keyboard = [
        [
            InlineKeyboardButton("🎮 10 ETB", callback_data="bet_10"),
            InlineKeyboardButton("🎮 20 ETB", callback_data="bet_20"),
        ],
        [InlineKeyboardButton("🎮 50 ETB", callback_data="bet_50")],
        [leaderboard_btn],
    ]
    return text, InlineKeyboardMarkup(keyboard)


def parse_bet_amount(callback_data: str) -> int | None:
    """Parse bet_* callback_data into an integer amount or None if not a bet."""
    if not callback_data.startswith("bet_"):
        return None
    try:
        return int(callback_data.split("_", 1)[1])
    except Exception:
        return None
