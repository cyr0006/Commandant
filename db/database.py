from datetime import timedelta
import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), "commandant.db")

def get_conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn

# ── Goal Records ──────────────────────────────────────────────────

def set_goal_status(user_id: str, username: str, date: str, status: str):
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO goal_records (user_id, username, date, status)
            VALUES (?, ?, ?, ?)
            ON CONFLICT(user_id, date) DO UPDATE SET 
                status = excluded.status,
                username = excluded.username
        """, (user_id, username, date, status))

def get_goal_status(user_id: str, date: str) -> str | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT status FROM goal_records WHERE user_id = ? AND date = ?",
            (user_id, date)
        ).fetchone()
    return row["status"] if row else None

def get_all_users() -> list[dict]:
    """Returns list of {user_id, username}"""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT DISTINCT user_id, username FROM goal_records"
        ).fetchall()
    return [{"user_id": r["user_id"], "username": r["username"]} for r in rows]

def get_user_records(user_id: str) -> dict:
    """Returns {date: status} for a user"""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT date, status FROM goal_records WHERE user_id = ? ORDER BY date",
            (user_id,)
        ).fetchall()
    return {r["date"]: r["status"] for r in rows}

def init_today_for_all_users(date: str):
    """Add empty record for today for all known users, skip if exists"""
    users = get_all_users()
    with get_conn() as conn:
        for user in users:
            conn.execute("""
                INSERT OR IGNORE INTO goal_records (user_id, username, date, status)
                VALUES (?, ?, ?, '')
            """, (user["user_id"], user["username"], date))

def finalize_yesterday(date: str):
    with get_conn() as conn:
        conn.execute("""
            UPDATE goal_records SET status = 'incomplete'
            WHERE date = ? AND status = ''
        """, (date,))

# ── Metadata ──────────────────────────────────────────────────────

def get_metadata(key: str) -> str | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT value FROM metadata WHERE key = ?", (key,)
        ).fetchone()
    return row["value"] if row else None

def set_metadata(key: str, value: str):
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO metadata (key, value) VALUES (?, ?)
            ON CONFLICT(key) DO UPDATE SET value = excluded.value
        """, (key, value))



# ── performance queries ──────────────────────────────────────────────────────
def performance_this_week() -> dict:
    from bot.utils import get_melbourne_date
    today = get_melbourne_date()
    monday = today - timedelta(days=today.weekday())  # weekday() is 0 on Monday
    
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT username,
                   COUNT(*) as total,
                   SUM(CASE WHEN status = 'complete' THEN 1 ELSE 0 END) as complete_count
            FROM goal_records
            WHERE date >= ? AND date <= ?
            GROUP BY user_id, username
        """, (str(monday), str(today))).fetchall()
    return {r["username"]: (r["complete_count"], r["total"]) for r in rows}
def performance_last_n_days(n: int) -> dict:
    """Returns {username: complete_count} for the last n days (rolling)"""
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT username, 
                   SUM(CASE WHEN status = 'complete' THEN 1 ELSE 0 END) as complete_count
            FROM goal_records
            WHERE date > date('now', ?)
            AND date <= date('now')
            GROUP BY user_id, username
        """, (f'-{n} days',)).fetchall()
    return {r["username"]: r["complete_count"] for r in rows}

def performance_all_time() -> dict:
    """Returns {username: (complete_count, total_days)}"""
    with get_conn() as conn:
        rows = conn.execute("""
            SELECT username,
                   COUNT(*) as total,
                   SUM(CASE WHEN status = 'complete' THEN 1 ELSE 0 END) as complete_count
            FROM goal_records
            GROUP BY user_id, username
        """).fetchall()
    return {r["username"]: (r["complete_count"], r["total"]) for r in rows}

def check_weekly_missed_goals(user_id: str, max_misses: int = 2):
    """Returns (over_limit: bool, miss_count: int) for current week"""
    with get_conn() as conn:
        row = conn.execute("""
            SELECT COUNT(*) as miss_count
            FROM goal_records
            WHERE user_id = ?
            AND (status = 'incomplete' OR status = '')
            AND date >= date('now', 'weekday 0', '-6 days')
        """, (user_id,)).fetchone()
    miss_count = row["miss_count"]
    return miss_count > max_misses, miss_count