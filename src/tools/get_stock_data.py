import logging
import yfinance as yf

logger = logging.getLogger(__name__)

SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_stock_data",
        "description": "מחזיר נתוני מניה עדכניים: מחיר, שינוי יומי, נפח, שווי שוק ו-52 שבועות גבוה/נמוך. למניות ישראליות הוסף .TA (לדוגמה TEVA.TA).",
        "parameters": {
            "type": "object",
            "properties": {
                "ticker": {
                    "type": "string",
                    "description": "סימול המניה, לדוגמה AAPL, TEVA.TA, TA35.TA",
                }
            },
            "required": ["ticker"],
        },
    },
}


def handler(ticker: str) -> dict:
    try:
        stock = yf.Ticker(ticker.upper())
        info = stock.info

        price = info.get("currentPrice") or info.get("regularMarketPrice")
        prev_close = info.get("previousClose") or info.get("regularMarketPreviousClose")
        change_pct = ((price - prev_close) / prev_close * 100) if price and prev_close else None

        return {
            "ticker": ticker.upper(),
            "name": info.get("longName") or info.get("shortName", ""),
            "price": round(price, 2) if price else None,
            "currency": info.get("currency", ""),
            "change_pct": round(change_pct, 2) if change_pct is not None else None,
            "volume": info.get("regularMarketVolume"),
            "market_cap": info.get("marketCap"),
            "week_52_high": info.get("fiftyTwoWeekHigh"),
            "week_52_low": info.get("fiftyTwoWeekLow"),
        }
    except Exception as e:
        logger.error("get_stock_data failed for %s: %s", ticker, e)
        return {"error": str(e)}
