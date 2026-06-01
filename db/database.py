import sqlite3
import os

DB_PATH = DB_PATH = os.path.join(os.path.dirname(__file__), "commandant.db")

def get_conn():
    """Get a connection to the SQLite database."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    return conn


#====================== Goal Records ======================
def set_goal_status(username: str, date: str, status: str):
    """Set a goal status for a user on a specific date."""
    with get_conn() as conn:
        conn.execute("""
            INSERT INTO goal_records (username, date, status)
            VALUES (?, ?, ?)
            ON CONFLICT(username, date) DO UPDATE SET status = excluded.status
        """, (username, date, status))


def get_goal_status(username: str, date: str) -> str | None:
    with get_conn() as conn:
        row = conn.execute(
            "SELECT status FROM goal_records WHERE username = ? AND date = ?",
            (username, date)
        ).fetchone()
    return row["status"] if row else None

def get_all_users() -> list[str]:
    with get_conn() as conn:
        rows = conn.execute("SELECT DISTINCT username FROM goal_records").fetchall()
    return [r["username"] for r in rows]


def get_user_records(username: str) -> dict:
    """Returns {date: status} for a user"""
    with get_conn() as conn:
        rows = conn.execute(
            "SELECT date, status FROM goal_records WHERE username = ? ORDER BY date",
            (username,)
        ).fetchall()
    return {r["date"]: r["status"] for r in rows}

def init_today_for_all_users(date: str):
    """Add empty record for today for all known users, skip if exists"""
    users = get_all_users()
    with get_conn() as conn:
        for user in users:
            conn.execute("""
                INSERT OR IGNORE INTO goal_records (username, date, status)
                VALUES (?, ?, '')
            """, (user, date))

def finalize_yesterday(date: str):
    """Mark all empty records for a date as incomplete"""
    with get_conn() as conn:
        conn.execute("""
            UPDATE goal_records SET status = 'incomplete'
            WHERE date = ? AND status = ''
        """, (date,))

# ===================== Metadata ==========================

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