import logging
import yfinance as yf

logger = logging.getLogger(__name__)

INDICES = {
    "S&P 500": "^GSPC",
    "Nasdaq": "^IXIC",
    "Dow Jones": "^DJI",
    'ת"א 35': "TA35.TA",
}


def get_market_summary() -> dict:
    results = {}
    for name, ticker in INDICES.items():
        try:
            info = yf.Ticker(ticker).info
            price = info.get("regularMarketPrice") or info.get("currentPrice")
            prev = info.get("regularMarketPreviousClose") or info.get("previousClose")
            change_pct = round((price - prev) / prev * 100, 2) if price and prev else None
            results[name] = {
                "ticker": ticker,
                "price": round(price, 2) if price else None,
                "change_pct": change_pct,
            }
        except Exception as e:
            logger.error("Failed to fetch %s (%s): %s", name, ticker, e)
            results[name] = {"error": str(e)}
    return results
