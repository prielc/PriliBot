import sqlite3
import threading
import logging
from pathlib import Path
from src.config.settings import DB_PATH

logger = logging.getLogger(__name__)

_lock = threading.Lock()
_connection: sqlite3.Connection | None = None


def get_connection() -> sqlite3.Connection:
    global _connection
    if _connection is None:
        with _lock:
            if _connection is None:
                Path(DB_PATH).parent.mkdir(parents=True, exist_ok=True)
                _connection = sqlite3.connect(DB_PATH, check_same_thread=False)
                _connection.row_factory = sqlite3.Row
                _connection.execute("PRAGMA journal_mode=WAL")
                _connection.execute("PRAGMA foreign_keys=ON")
                logger.info("Database connection established: %s", DB_PATH)
    return _connection


def init_db() -> None:
    conn = get_connection()
    with _lock:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                telegram_id   INTEGER UNIQUE NOT NULL,
                username      TEXT,
                first_name    TEXT,
                is_active     INTEGER NOT NULL DEFAULT 1,
                created_at    TEXT NOT NULL DEFAULT (datetime('now'))
            );

            CREATE TABLE IF NOT EXISTS watchlist (
                id          INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id     INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                ticker      TEXT NOT NULL,
                notes       TEXT,
                created_at  TEXT NOT NULL DEFAULT (datetime('now')),
                UNIQUE(user_id, ticker)
            );

            CREATE TABLE IF NOT EXISTS alerts (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id       INTEGER NOT NULL REFERENCES users(id) ON DELETE CASCADE,
                ticker        TEXT NOT NULL,
                alert_type    TEXT NOT NULL CHECK(alert_type IN ('price_above', 'price_below', 'news')),
                price_target  REAL,
                is_active     INTEGER NOT NULL DEFAULT 1,
                created_at    TEXT NOT NULL DEFAULT (datetime('now'))
            );
        """)
        conn.commit()
    logger.info("Database initialized successfully")


def execute(query: str, params: tuple = ()) -> sqlite3.Cursor:
    with _lock:
        return get_connection().execute(query, params)


def commit() -> None:
    with _lock:
        get_connection().commit()
