import json
import sqlite3
from pathlib import Path
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_GET
from django.conf import settings

DB_FILE = str(Path(settings.BASE_DIR).parent / "usage.db")


def _get_conn():
    return sqlite3.connect(DB_FILE)


@require_GET
def leaderboard_view(request):
    """Return top users by coin as a simple JSON list suitable for the Mini App.

    Response format:
    {
      "items": [
        {"rank": 1, "player": "Alice", "points": 1200, "prize": "500 ETB"},
        ...
      ]
    }
    """
    # Limit to avoid huge payloads
    limit = int(request.GET.get("limit", 50))
    limit = max(1, min(limit, 200))

    conn = _get_conn()
    try:
        cur = conn.cursor()
        # Ensure coin and username columns exist (defensive)
        cur.execute("PRAGMA table_info(users)")
        cols = {row[1] for row in cur.fetchall()}
        if "coin" not in cols:
            # No leaderboard data yet
            return _cors(JsonResponse({"items": []}))
        # Query top users by coin desc
        # Prefer a display name: username if set, else user_id
        select_username = "COALESCE(NULLIF(username, ''), CAST(user_id AS TEXT))"
        cur.execute(
            f"""
            SELECT user_id, {select_username} AS display_name, COALESCE(coin, 0) AS coin
            FROM users
            ORDER BY coin DESC, user_id ASC
            LIMIT ?
            """,
            (limit,),
        )
        rows = cur.fetchall()
    finally:
        conn.close()

    items = []
    for idx, (user_id, display_name, coin) in enumerate(rows, start=1):
        prize = _prize_for_rank(idx)
        items.append({
            "rank": idx,
            "player": display_name,
            "points": float(coin),
            "prize": prize,
        })

    return _cors(JsonResponse({"items": items}))


def _prize_for_rank(rank: int) -> str:
    # Simple demo prize tiers; adjust to your business rules
    if rank == 1:
        return "500 ETB"
    if rank == 2:
        return "300 ETB"
    if rank == 3:
        return "150 ETB"
    if rank <= 10:
        return "50 ETB"
    return "—"


def _cors(resp: HttpResponse) -> HttpResponse:
    # Allow cross-origin reads for the Mini App during development
    resp["Access-Control-Allow-Origin"] = "*"
    resp["Cache-Control"] = "no-store"
    return resp
