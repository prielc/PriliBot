import os
import pytest
from unittest.mock import AsyncMock, MagicMock, patch

os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test")
os.environ.setdefault("GROQ_API_KEY", "test")


def _make_update(text: str, user_id: int = 1, username: str = "test", first_name: str = "Test") -> MagicMock:
    user = MagicMock()
    user.id = user_id
    user.username = username
    user.first_name = first_name

    message = MagicMock()
    message.text = text
    message.reply_text = AsyncMock()

    update = MagicMock()
    update.effective_user = user
    update.effective_chat.id = user_id
    update.message = message
    return update


def _make_context() -> MagicMock:
    context = MagicMock()
    context.bot.send_chat_action = AsyncMock()
    return context


# ------------------------------------------------------------------
# /start
# ------------------------------------------------------------------

@pytest.mark.asyncio
async def test_start_registers_user(tmp_path):
    os.environ["DB_PATH"] = str(tmp_path / "test.db")
    import importlib, src.config.settings as s, src.db.database as db_mod
    importlib.reload(s)
    importlib.reload(db_mod)
    db_mod.init_db()

    from src.bot.handler import start_command
    update = _make_update("", user_id=999, first_name="Priel")
    await start_command(update, _make_context())

    row = db_mod.execute("SELECT * FROM users WHERE telegram_id = 999").fetchone()
    assert row is not None
    update.message.reply_text.assert_called_once()
    assert "Priel" in update.message.reply_text.call_args[0][0]


# ------------------------------------------------------------------
# /help
# ------------------------------------------------------------------

@pytest.mark.asyncio
async def test_help_sends_message():
    from src.bot.handler import help_command
    update = _make_update("")
    await help_command(update, _make_context())
    update.message.reply_text.assert_called_once()
    text = update.message.reply_text.call_args[0][0]
    assert "מניות" in text
    assert "חדשות" in text


# ------------------------------------------------------------------
# message_handler
# ------------------------------------------------------------------

@pytest.mark.asyncio
async def test_message_handler_calls_agent():
    with patch("groq.Groq"):
        from src.agent.agent import PriliAgent
        import src.bot.handler as h

        agent = PriliAgent()
        agent.process_message = MagicMock(return_value="תשובה מהבוט")
        h._agent = agent

        update = _make_update("מה המחיר של AAPL?")
        await h.message_handler(update, _make_context())

        agent.process_message.assert_called_once_with(1, "מה המחיר של AAPL?")
        update.message.reply_text.assert_called_once_with("תשובה מהבוט")


@pytest.mark.asyncio
async def test_message_handler_returns_error_on_exception():
    with patch("groq.Groq"):
        from src.agent.agent import PriliAgent
        import src.bot.handler as h

        agent = PriliAgent()
        agent.process_message = MagicMock(side_effect=Exception("groq down"))
        h._agent = agent

        update = _make_update("שאלה")
        await h.message_handler(update, _make_context())

        reply = update.message.reply_text.call_args[0][0]
        assert "שגיאה" in reply


# ------------------------------------------------------------------
# setup
# ------------------------------------------------------------------

def test_setup_registers_handlers():
    with patch("groq.Groq"):
        from src.agent.agent import PriliAgent
        from src.bot.handler import setup

        agent = PriliAgent()
        app = MagicMock()
        app.job_queue = MagicMock()

        setup(app, agent)

        assert app.add_handler.call_count == 3
        app.job_queue.run_daily.assert_called_once()
