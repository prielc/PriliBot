import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test")
os.environ.setdefault("GROQ_API_KEY", "test")


def _setup_db(tmp_path):
    os.environ["DB_PATH"] = str(tmp_path / "test.db")
    import importlib, src.config.settings as s, src.db.database as db
    importlib.reload(s)
    importlib.reload(db)
    db.init_db()
    db.execute("INSERT INTO users (telegram_id, username, first_name) VALUES (99, 'u', 'T')")
    db.commit()
    return db


def _insert_alert(db, alert_type: str, ticker: str, price_target: float):
    user_id = db.execute("SELECT id FROM users WHERE telegram_id = 99").fetchone()["id"]
    db.execute(
        "INSERT INTO alerts (user_id, ticker, alert_type, price_target) VALUES (?, ?, ?, ?)",
        (user_id, ticker, alert_type, price_target),
    )
    db.commit()


# ------------------------------------------------------------------
# price_above alert
# ------------------------------------------------------------------

@pytest.mark.asyncio
async def test_price_above_triggers_when_condition_met(tmp_path):
    db = _setup_db(tmp_path)
    _insert_alert(db, "price_above", "AAPL", 200.0)

    bot = MagicMock()
    bot.send_message = AsyncMock()

    with patch("src.services.alerts._get_price", return_value=205.0):
        from src.services.alerts import check_alerts
        await check_alerts(bot)

    bot.send_message.assert_called_once()
    msg = bot.send_message.call_args[1]["text"]
    assert "AAPL" in msg
    assert "עלה מעל" in msg

    row = db.execute("SELECT is_active FROM alerts WHERE ticker = 'AAPL'").fetchone()
    assert row["is_active"] == 0


@pytest.mark.asyncio
async def test_price_above_does_not_trigger_when_below(tmp_path):
    db = _setup_db(tmp_path)
    _insert_alert(db, "price_above", "AAPL", 200.0)

    bot = MagicMock()
    bot.send_message = AsyncMock()

    with patch("src.services.alerts._get_price", return_value=190.0):
        from src.services.alerts import check_alerts
        await check_alerts(bot)

    bot.send_message.assert_not_called()
    row = db.execute("SELECT is_active FROM alerts WHERE ticker = 'AAPL'").fetchone()
    assert row["is_active"] == 1


# ------------------------------------------------------------------
# price_below alert
# ------------------------------------------------------------------

@pytest.mark.asyncio
async def test_price_below_triggers_when_condition_met(tmp_path):
    db = _setup_db(tmp_path)
    _insert_alert(db, "price_below", "TEVA", 15.0)

    bot = MagicMock()
    bot.send_message = AsyncMock()

    with patch("src.services.alerts._get_price", return_value=13.5):
        from src.services.alerts import check_alerts
        await check_alerts(bot)

    bot.send_message.assert_called_once()
    msg = bot.send_message.call_args[1]["text"]
    assert "TEVA" in msg
    assert "ירד מתחת" in msg


# ------------------------------------------------------------------
# no alerts
# ------------------------------------------------------------------

@pytest.mark.asyncio
async def test_no_alerts_does_nothing(tmp_path):
    _setup_db(tmp_path)

    bot = MagicMock()
    bot.send_message = AsyncMock()

    from src.services.alerts import check_alerts
    await check_alerts(bot)

    bot.send_message.assert_not_called()


# ------------------------------------------------------------------
# price fetch failure — alert stays active
# ------------------------------------------------------------------

@pytest.mark.asyncio
async def test_price_fetch_failure_keeps_alert_active(tmp_path):
    db = _setup_db(tmp_path)
    _insert_alert(db, "price_above", "BAD", 100.0)

    bot = MagicMock()
    bot.send_message = AsyncMock()

    with patch("src.services.alerts._get_price", return_value=None):
        from src.services.alerts import check_alerts
        await check_alerts(bot)

    bot.send_message.assert_not_called()
    row = db.execute("SELECT is_active FROM alerts WHERE ticker = 'BAD'").fetchone()
    assert row["is_active"] == 1


# ------------------------------------------------------------------
# alerts_job registered in setup
# ------------------------------------------------------------------

def test_alerts_job_registered_in_setup():
    with patch("groq.Groq"):
        from src.agent.agent import PriliAgent
        from src.bot.handler import setup

        agent = PriliAgent()
        app = MagicMock()
        app.job_queue = MagicMock()

        setup(app, agent)

        run_repeating_calls = app.job_queue.run_repeating.call_args_list
        names = [c[1].get("name") for c in run_repeating_calls]
        assert "alerts" in names
