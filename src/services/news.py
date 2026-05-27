import logging
import feedparser
from datetime import datetime

logger = logging.getLogger(__name__)

FINANCIAL_NEWS_RSS = "https://news.google.com/rss/search?q=כלכלה+שוק+מניות&hl=iw&gl=IL&ceid=IL:iw"


def get_financial_news(max_results: int = 5) -> list[dict]:
    try:
        feed = feedparser.parse(FINANCIAL_NEWS_RSS)
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
            })
        return articles
    except Exception as e:
        logger.error("get_financial_news failed: %s", e)
        return []
