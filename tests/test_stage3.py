import os
import pytest
from unittest.mock import patch, MagicMock

os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test")
os.environ.setdefault("GROQ_API_KEY", "test")


# ------------------------------------------------------------------
# get_stock_data
# ------------------------------------------------------------------

def test_get_stock_data_returns_expected_keys():
    from src.tools.get_stock_data import handler
    mock_info = {
        "longName": "Apple Inc.",
        "currentPrice": 200.0,
        "previousClose": 195.0,
        "currency": "USD",
        "regularMarketVolume": 50000000,
        "marketCap": 3000000000000,
        "fiftyTwoWeekHigh": 220.0,
        "fiftyTwoWeekLow": 160.0,
    }
    with patch("yfinance.Ticker") as mock_ticker:
        mock_ticker.return_value.info = mock_info
        result = handler("AAPL")

    assert result["ticker"] == "AAPL"
    assert result["price"] == 200.0
    assert result["change_pct"] == round((200 - 195) / 195 * 100, 2)
    assert "error" not in result


def test_get_stock_data_handles_error():
    from src.tools.get_stock_data import handler
    with patch("yfinance.Ticker", side_effect=Exception("network error")):
        result = handler("INVALID")
    assert "error" in result


# ------------------------------------------------------------------
# get_news
# ------------------------------------------------------------------

def test_get_news_returns_articles():
    from src.tools.get_news import handler
    mock_entry = MagicMock()
    mock_entry.title = "שוק המניות עלה"
    mock_entry.source = {"title": "Ynet"}
    mock_entry.link = "https://example.com"
    mock_entry.published_parsed = (2026, 5, 27, 10, 0, 0, 0, 0, 0)

    mock_feed = MagicMock()
    mock_feed.entries = [mock_entry]

    with patch("feedparser.parse", return_value=mock_feed):
        result = handler("שוק המניות", max_results=3)

    assert result["total"] == 1
    assert result["articles"][0]["title"] == "שוק המניות עלה"


def test_get_news_handles_error():
    from src.tools.get_news import handler
    with patch("feedparser.parse", side_effect=Exception("timeout")):
        result = handler("test")
    assert "error" in result


# ------------------------------------------------------------------
# execute_sql
# ------------------------------------------------------------------

def test_execute_sql_blocks_drop():
    from src.tools.execute_sql import handler
    result = handler("DROP TABLE users")
    assert "error" in result


def test_execute_sql_blocks_create():
    from src.tools.execute_sql import handler
    result = handler("CREATE TABLE x (id INTEGER)")
    assert "error" in result


def test_execute_sql_blocks_non_dml():
    from src.tools.execute_sql import handler
    result = handler("PRAGMA journal_mode=WAL")
    assert "error" in result


def test_execute_sql_select(tmp_path):
    os.environ["DB_PATH"] = str(tmp_path / "test.db")
    import importlib, src.config.settings as s, src.db.database as db
    importlib.reload(s)
    importlib.reload(db)
    db.init_db()

    from src.tools.execute_sql import handler
    result = handler("SELECT * FROM users")
    assert "rows" in result
    assert result["count"] == 0


def test_execute_sql_insert(tmp_path):
    os.environ["DB_PATH"] = str(tmp_path / "test2.db")
    import importlib, src.config.settings as s, src.db.database as db
    importlib.reload(s)
    importlib.reload(db)
    db.init_db()

    from src.tools.execute_sql import handler
    result = handler("INSERT INTO users (telegram_id, username, first_name) VALUES (1, 'u', 'Test')")
    assert result["affected_rows"] == 1


# ------------------------------------------------------------------
# get_schema
# ------------------------------------------------------------------

def test_get_schema_returns_tables(tmp_path):
    os.environ["DB_PATH"] = str(tmp_path / "schema_test.db")
    import importlib, src.config.settings as s, src.db.database as db
    importlib.reload(s)
    importlib.reload(db)
    db.init_db()

    from src.tools.get_schema import handler
    result = handler()
    assert "tables" in result
    assert "users" in result["tables"]
    assert "watchlist" in result["tables"]
    assert "alerts" in result["tables"]


# ------------------------------------------------------------------
# save_memory / search_memory
# ------------------------------------------------------------------

def test_save_and_search_memory(tmp_path):
    from src.config import settings
    settings.MEMORY_DIR = tmp_path / "memory"

    from src.tools.save_memory import handler as save
    from src.tools.search_memory import handler as search

    save("המשתמש מעדיף מניות דיבידנד")
    save("אסטרטגיה: השקעה לטווח ארוך")

    result = search("דיבידנד")
    assert result["total"] >= 1
    assert any("דיבידנד" in r["content"] for r in result["results"])


def test_search_memory_empty(tmp_path):
    from src.config import settings
    settings.MEMORY_DIR = tmp_path / "empty_memory"

    from src.tools.search_memory import handler as search
    result = search("כלום")
    assert result["total"] == 0
    assert result["results"] == []


# ------------------------------------------------------------------
# register_all_tools
# ------------------------------------------------------------------

def test_register_all_tools():
    with patch("groq.Groq"):
        from src.agent.agent import PriliAgent
        from src.tools import register_all_tools

        agent = PriliAgent()
        register_all_tools(agent)

        assert len(agent._tools) == 6
        tool_names = {t["function"]["name"] for t in agent._tools}
        assert tool_names == {
            "get_stock_data", "get_news", "get_schema",
            "execute_sql", "save_memory", "search_memory",
        }
