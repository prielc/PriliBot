import logging
from src.config.settings import MEMORY_DIR

logger = logging.getLogger(__name__)

SCHEMA = {
    "type": "function",
    "function": {
        "name": "search_memory",
        "description": "מחפש בזיכרון ארוך-טווח (העדפות, קריטריונים, מידע שנשמר בשיחות קודמות).",
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "מילות חיפוש",
                }
            },
            "required": ["query"],
        },
    },
}


def handler(query: str) -> dict:
    try:
        if not MEMORY_DIR.exists():
            return {"results": [], "total": 0}

        query_lower = query.lower()
        results = []

        for memory_file in sorted(MEMORY_DIR.glob("*.md"), reverse=True):
            lines = memory_file.read_text(encoding="utf-8").splitlines()
            for line in lines:
                if query_lower in line.lower():
                    results.append({"date": memory_file.stem, "content": line.strip()})

        return {"results": results[:10], "total": len(results)}
    except Exception as e:
        logger.error("search_memory failed: %s", e)
        return {"error": str(e)}
