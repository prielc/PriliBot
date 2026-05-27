import logging
import feedparser
from datetime import datetime

logger = logging.getLogger(__name__)

GOOGLE_NEWS_RSS = "https://news.google.com/rss/search?q={query}&hl=iw&gl=IL&ceid=IL:iw"

SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_news",
        "description": "מביא חדשות עדכניות לפי נושא או סימול מניה מ-Google News.",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "נושא החיפוש, לדוגמה 'AAPL' או 'שוק ההון' או 'ריבית פד",
                },
                "max_results": {
                    "type": "integer",
                    "description": "מספר מקסימלי של תוצאות (ברירת מחדל: 5)",
                    "default": 5,
                },
            },
            "required": ["query"],
        },
    },
}


def handler(query: str, max_results: int = 5) -> dict:
    try:
        url = GOOGLE_NEWS_RSS.format(query=query.replace(" ", "+"))
        feed = feedparser.parse(url)

        articles = []
        for entry in feed.entries[:max_results]:
            published = ""
            if hasattr(entry, "published_parsed") and entry.published_parsed:
                published = datetime(*entry.published_parsed[:6]).strftime("%Y-%m-%d %H:%M")
            source = entry.source if hasattr(entry, "source") else {}
            articles.append({
                "title": entry.title if hasattr(entry, "title") else "",
                "source": source.get("title", "") if isinstance(source, dict) else getattr(source, "title", ""),
                "published": published,
                "link": entry.link if hasattr(entry, "link") else "",
            })

        return {"query": query, "articles": articles, "total": len(articles)}
    except Exception as e:
        logger.error("get_news failed for query '%s': %s", query, e)
        return {"error": str(e)}
