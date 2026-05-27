import os
import sqlite3
import tempfile
import pytest

os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test")
os.environ.setdefault("GROQ_API_KEY", "test")


def test_settings_loads():
    from src.config.settings import GROQ_MODEL, MAX_HISTORY_MESSAGES, SYSTEM_PROMPT, TIMEZONE
    assert GROQ_MODEL == "llama-3.3-70b-versatile"
    assert MAX_HISTORY_MESSAGES == 40
    assert "עברית" in SYSTEM_PROMPT
    assert TIMEZONE == "Asia/Jerusalem"


def test_db_init_creates_tables(tmp_path):
    import src.db.database as db_module
    db_module._connection = None
    os.environ["DB_PATH"] = str(tmp_path / "test.db")

    # reload settings so DB_PATH picks up the new env var
    import importlib, src.config.settings as s
    importlib.reload(s)
    import src.db.database as db
    importlib.reload(db)

    db.init_db()
    conn = db.get_connection()

    tables = {row[0] for row in conn.execute(
        "SELECT name FROM sqlite_master WHERE type='table'"
    )}
    assert {"users", "watchlist", "alerts"}.issubset(tables)


def test_db_wal_mode(tmp_path):
    import src.db.database as db_module
    db_module._connection = None
    os.environ["DB_PATH"] = str(tmp_path / "wal_test.db")

    import importlib, src.config.settings as s
    importlib.reload(s)
    import src.db.database as db
    importlib.reload(db)

    db.init_db()
    mode = db.execute("PRAGMA journal_mode").fetchone()[0]
    assert mode == "wal"


def test_db_insert_user(tmp_path):
    import src.db.database as db_module
    db_module._connection = None
    os.environ["DB_PATH"] = str(tmp_path / "insert_test.db")

    import importlib, src.config.settings as s
    importlib.reload(s)
    import src.db.database as db
    importlib.reload(db)

    db.init_db()
    db.execute(
        "INSERT INTO users (telegram_id, username, first_name) VALUES (?, ?, ?)",
        (123456, "testuser", "Test"),
    )
    db.commit()
    row = db.execute("SELECT * FROM users WHERE telegram_id = 123456").fetchone()
    assert row is not None
    assert row["first_name"] == "Test"
