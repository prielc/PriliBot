import os
import pytest
from unittest.mock import MagicMock, patch, AsyncMock

os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test")
os.environ.setdefault("GROQ_API_KEY", "test")


# ------------------------------------------------------------------
# stocks service
# ------------------------------------------------------------------

def test_get_market_summary_returns_all_indices():
    from src.services.stocks import get_market_summary, INDICES
    mock_info = {
        "regularMarketPrice": 5000.0,
        "regularMarketPreviousClose": 4900.0,
    }
    with patch("yfinance.Ticker") as mock_ticker:
        mock_ticker.return_value.info = mock_info
        result = get_market_summary()

    assert set(result.keys()) == set(INDICES.keys())
    for name, data in result.items():
        assert "price" in data
        assert "change_pct" in data


def test_get_market_summary_handles_partial_failure():
    from src.services.stocks import get_market_summary

    def side_effect(ticker):
        m = MagicMock()
        if ticker == "^GSPC":
            raise Exception("network error")
        m.info = {"regularMarketPrice": 100.0, "regularMarketPreviousClose": 95.0}
        return m

    with patch("yfinance.Ticker", side_effect=side_effect):
        result = get_market_summary()

    assert "error" in result["S&P 500"]
    assert "price" in result["Nasdaq"]


# ------------------------------------------------------------------
# news service
# ------------------------------------------------------------------

def test_get_financial_news_returns_articles():
    from src.services.news import get_financial_news

    mock_entry = MagicMock()
    mock_entry.title = "הכלכלה צומחת"
    mock_entry.source = {"title": "TheMarker"}
    mock_entry.published_parsed = (2026, 5, 27, 8, 0, 0, 0, 0, 0)

    mock_feed = MagicMock()
    mock_feed.entries = [mock_entry]

    with patch("feedparser.parse", return_value=mock_feed):
        articles = get_financial_news(max_results=3)

    assert len(articles) == 1
    assert articles[0]["title"] == "הכלכלה צומחת"


def test_get_financial_news_returns_empty_on_error():
    from src.services.news import get_financial_news
    with patch("feedparser.parse", side_effect=Exception("timeout")):
        result = get_financial_news()
    assert result == []


# ------------------------------------------------------------------
# generate_daily_digest
# ------------------------------------------------------------------

def test_generate_daily_digest_returns_text():
    with patch("groq.Groq"):
        from src.agent.agent import PriliAgent

        agent = PriliAgent()

        mock_market = {"S&P 500": {"price": 5000, "change_pct": 0.5}}
        mock_news = [{"title": "שוק עולה", "source": "Ynet"}]
        mock_response = MagicMock()
        mock_response.choices[0].message.content = "הבוקר השווקים עלו."

        with patch("src.services.stocks.get_market_summary", return_value=mock_market), \
             patch("src.services.news.get_financial_news", return_value=mock_news), \
             patch.object(agent._client.chat.completions, "create", return_value=mock_response):
            result = agent.generate_daily_digest()

    assert result == "הבוקר השווקים עלו."


# ------------------------------------------------------------------
# daily_digest_job
# ------------------------------------------------------------------

@pytest.mark.asyncio
async def test_daily_digest_job_sends_message(tmp_path):
    os.environ["DB_PATH"] = str(tmp_path / "test.db")
    import importlib, src.config.settings as s, src.db.database as db_mod
    importlib.reload(s)
    importlib.reload(db_mod)
    db_mod.init_db()
    db_mod.execute("INSERT INTO users (telegram_id, username, first_name) VALUES (12345, 'u', 'T')")
    db_mod.commit()

    with patch("groq.Groq"):
        from src.agent.agent import PriliAgent
        import src.bot.handler as h

        agent = PriliAgent()
        agent.generate_daily_digest = MagicMock(return_value="סקירת הבוקר כאן.")
        h._agent = agent

        context = MagicMock()
        context.bot.send_message = AsyncMock()

        await h.daily_digest_job(context)

        context.bot.send_message.assert_called_once()
        call_kwargs = context.bot.send_message.call_args
        assert "סקירת הבוקר" in call_kwargs[1]["text"]
