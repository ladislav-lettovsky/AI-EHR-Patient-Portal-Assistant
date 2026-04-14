"""SQLite connection management."""

from __future__ import annotations

import sqlite3

from .config import DATA_DIR

_connection: sqlite3.Connection | None = None


def get_connection() -> sqlite3.Connection:
    global _connection
    if _connection is None:
        db_path = DATA_DIR / "health_portal.db"
        _connection = sqlite3.connect(str(db_path))
        _connection.row_factory = sqlite3.Row
    return _connection


def sql_query(q: str, params: tuple = ()) -> list[dict]:
    """Execute a parameterized SQL query and return rows as dicts."""
    con = get_connection()
    rows = con.execute(q, tuple(params)).fetchall()
    return [dict(row) for row in rows]


def close() -> None:
    global _connection
    if _connection:
        _connection.close()
        _connection = None
