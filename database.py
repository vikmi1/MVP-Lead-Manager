import sqlite3
from datetime import datetime, timezone
from typing import Optional


def _get_conn(db_path: str) -> sqlite3.Connection:
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    return conn


def init_db(db_path: str) -> None:
    with _get_conn(db_path) as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS leads (
                id         INTEGER PRIMARY KEY AUTOINCREMENT,
                created_at DATETIME NOT NULL,
                name       TEXT,
                contact    TEXT NOT NULL,
                source     TEXT,
                comment    TEXT,
                consent    BOOLEAN NOT NULL
            )
        """)
        conn.commit()


def create_lead(
    db_path: str,
    name: Optional[str],
    contact: str,
    source: Optional[str],
    comment: Optional[str],
    consent: bool,
) -> int:
    created_at = datetime.now(timezone.utc).isoformat()
    with _get_conn(db_path) as conn:
        cursor = conn.execute(
            """INSERT INTO leads (created_at, name, contact, source, comment, consent)
               VALUES (?, ?, ?, ?, ?, ?)""",
            (created_at, name, contact, source, comment, consent),
        )
        conn.commit()
        return cursor.lastrowid


def get_leads(db_path: str, limit: int = 50, offset: int = 0) -> list[dict]:
    with _get_conn(db_path) as conn:
        rows = conn.execute(
            "SELECT * FROM leads ORDER BY created_at DESC LIMIT ? OFFSET ?",
            (limit, offset),
        ).fetchall()
    return [dict(row) for row in rows]


def delete_lead(db_path: str, lead_id: int) -> bool:
    with _get_conn(db_path) as conn:
        cursor = conn.execute("DELETE FROM leads WHERE id = ?", (lead_id,))
        conn.commit()
        return cursor.rowcount > 0
