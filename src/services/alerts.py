import logging
import yfinance as yf
from telegram import Bot
from src.db import database as db

logger = logging.getLogger(__name__)


async def check_alerts(bot: Bot) -> None:
    rows = db.execute(
        "SELECT a.id, a.user_id, a.ticker, a.alert_type, a.price_target, u.telegram_id "
        "FROM alerts a JOIN users u ON a.user_id = u.id "
        "WHERE a.is_active = 1"
    ).fetchall()

    if not rows:
        return

    for row in rows:
        alert_id = row["id"]
        ticker = row["ticker"]
        alert_type = row["alert_type"]
        price_target = row["price_target"]
        telegram_id = row["telegram_id"]

        try:
            price = _get_price(ticker)
            if price is None:
                continue

            triggered = (
                (alert_type == "price_above" and price >= price_target) or
                (alert_type == "price_below" and price <= price_target)
            )

            if triggered:
                direction = "עלה מעל" if alert_type == "price_above" else "ירד מתחת ל"
                message = (
                    f"🔔 *התראה: {ticker}*\n"
                    f"המחיר {direction} {price_target}\n"
                    f"מחיר נוכחי: {price}"
                )
                await bot.send_message(chat_id=telegram_id, text=message, parse_mode="Markdown")
                db.execute("UPDATE alerts SET is_active = 0 WHERE id = ?", (alert_id,))
                db.commit()
                logger.info("Alert %d triggered for %s @ %s", alert_id, ticker, price)

        except Exception as e:
            logger.error("Failed to check alert %d (%s): %s", alert_id, ticker, e)


def _get_price(ticker: str) -> float | None:
    try:
        info = yf.Ticker(ticker).info
        return info.get("currentPrice") or info.get("regularMarketPrice")
    except Exception as e:
        logger.error("Price fetch failed for %s: %s", ticker, e)
        return None
