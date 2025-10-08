import json
import sqlite3
from pathlib import Path
from django.http import JsonResponse, HttpResponse
from django.views.decorators.http import require_GET, require_http_methods
from django.conf import settings
from bots.deposit import ensure_admin_txns_table

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


# --------------------------
# Admin: Deposits moderation
# --------------------------

def _is_admin(request) -> bool:
    token = request.headers.get("X-Admin-Token") or request.GET.get("admin_token")
    expected = (getattr(settings, "ADMIN_API_TOKEN", None) or "").strip()
    return bool(expected) and token == expected


@require_GET
def list_pending_deposits(request):
    if not _is_admin(request):
        return _cors(JsonResponse({"error": "unauthorized"}, status=401))
    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            SELECT id, user_id, amount, method, reference, status, created_at
            FROM deposits
            WHERE status = 'pending'
            ORDER BY created_at ASC
            """
        )
        rows = cur.fetchall()
    finally:
        conn.close()
    items = [
        {
            "id": r[0],
            "user_id": r[1],
            "amount": r[2],
            "method": r[3],
            "reference": r[4],
            "status": r[5],
            "created_at": r[6],
        }
        for r in rows
    ]
    return _cors(JsonResponse({"items": items}))


@require_http_methods(["POST"])
def approve_deposit(request, deposit_id: int):
    if not _is_admin(request):
        return _cors(JsonResponse({"error": "unauthorized"}, status=401))

    conn = _get_conn()
    try:
        cur = conn.cursor()
        # Fetch deposit
        cur.execute("SELECT user_id, amount, status FROM deposits WHERE id = ?", (deposit_id,))
        row = cur.fetchone()
        if not row:
            return _cors(JsonResponse({"error": "not_found"}, status=404))
        user_id, amount, status = row
        if status != "pending":
            return _cors(JsonResponse({"error": "invalid_state"}, status=400))

        # Mark approved and credit balance
        cur.execute(
            "UPDATE deposits SET status='approved', approved_at=CURRENT_TIMESTAMP WHERE id = ?",
            (deposit_id,),
        )
        # Ensure users table has balance columns
        cur.execute("PRAGMA table_info(users)")
        cols = {c[1] for c in cur.fetchall()}
        if "balance" not in cols:
            cur.execute("ALTER TABLE users ADD COLUMN balance REAL DEFAULT 0")
        # Credit balance
        cur.execute(
            "UPDATE users SET balance = COALESCE(balance, 0) + ? WHERE user_id = ?",
            (float(amount), int(user_id)),
        )
        conn.commit()
    finally:
        conn.close()

    return _cors(JsonResponse({"ok": True}))


# ---------------------------------
# Admin: Manage admin-provided TXNs
# ---------------------------------

@require_GET
def list_admin_txns(request):
    if not _is_admin(request):
        return _cors(JsonResponse({"error": "unauthorized"}, status=401))
    ensure_admin_txns_table()

    only_unused = request.GET.get("unused") in {"1", "true", "True"}
    method = (request.GET.get("method") or "").strip().lower() or None

    conn = _get_conn()
    try:
        cur = conn.cursor()
        q = "SELECT id, method, reference, amount, used_by, used_at, notes FROM admin_txns"
        params = []
        where = []
        if only_unused:
            where.append("used_by IS NULL")
        if method:
            where.append("method = ?")
            params.append(method)
        if where:
            q += " WHERE " + " AND ".join(where)
        q += " ORDER BY used_by IS NOT NULL, id DESC"
        cur.execute(q, params)
        rows = cur.fetchall()
    finally:
        conn.close()

    items = [
        {
            "id": r[0],
            "method": r[1],
            "reference": r[2],
            "amount": r[3],
            "used_by": r[4],
            "used_at": r[5],
            "notes": r[6],
        }
        for r in rows
    ]
    return _cors(JsonResponse({"items": items}))


@require_http_methods(["POST"])
def add_admin_txn(request):
    if not _is_admin(request):
        return _cors(JsonResponse({"error": "unauthorized"}, status=401))
    ensure_admin_txns_table()

    try:
        payload = json.loads(request.body.decode("utf-8") or "{}")
    except Exception:
        return _cors(JsonResponse({"error": "invalid_json"}, status=400))

    method = (payload.get("method") or "").strip().lower()
    reference = (payload.get("reference") or payload.get("ref") or "").strip()
    amount = payload.get("amount")
    notes = payload.get("notes")
    if not method or not reference:
        return _cors(JsonResponse({"error": "missing_fields"}, status=400))

    conn = _get_conn()
    try:
        cur = conn.cursor()
        cur.execute(
            """
            INSERT OR IGNORE INTO admin_txns (method, reference, amount, notes)
            VALUES (?, ?, ?, ?)
            """,
            (method, reference, float(amount) if amount is not None else None, notes),
        )
        conn.commit()
    finally:
        conn.close()
    return _cors(JsonResponse({"ok": True}))


@require_http_methods(["POST"])
def bulk_add_admin_txns(request):
    if not _is_admin(request):
        return _cors(JsonResponse({"error": "unauthorized"}, status=401))
    ensure_admin_txns_table()

    raw = request.body.decode("utf-8", errors="ignore")
    added = 0
    skipped = 0
    conn = _get_conn()
    try:
        cur = conn.cursor()
        # Accept either JSON list or CSV (method,reference,amount,notes)
        try:
            data = json.loads(raw)
            if isinstance(data, list):
                for item in data:
                    method = (item.get("method") or "").strip().lower()
                    reference = (item.get("reference") or item.get("ref") or "").strip()
                    amount = item.get("amount")
                    notes = item.get("notes")
                    if not method or not reference:
                        skipped += 1
                        continue
                    try:
                        cur.execute(
                            "INSERT OR IGNORE INTO admin_txns (method, reference, amount, notes) VALUES (?, ?, ?, ?)",
                            (method, reference, float(amount) if amount is not None else None, notes),
                        )
                        added += cur.rowcount and 1 or 0
                    except Exception:
                        skipped += 1
                conn.commit()
                return _cors(JsonResponse({"ok": True, "added": added, "skipped": skipped}))
        except Exception:
            pass

        # CSV fallback
        for line in raw.splitlines():
            line = line.strip()
            if not line or line.startswith("#"):
                continue
            parts = [p.strip() for p in line.split(",")]
            if len(parts) < 2:
                skipped += 1
                continue
            method, reference = parts[0].lower(), parts[1]
            amount = None
            notes = None
            if len(parts) >= 3 and parts[2] != "":
                try:
                    amount = float(parts[2])
                except Exception:
                    amount = None
            if len(parts) >= 4:
                notes = parts[3]
            try:
                cur.execute(
                    "INSERT OR IGNORE INTO admin_txns (method, reference, amount, notes) VALUES (?, ?, ?, ?)",
                    (method, reference, amount, notes),
                )
                added += cur.rowcount and 1 or 0
            except Exception:
                skipped += 1
        conn.commit()
    finally:
        conn.close()
    return _cors(JsonResponse({"ok": True, "added": added, "skipped": skipped}))
