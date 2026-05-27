import logging
import re
from src.db.database import execute, commit

logger = logging.getLogger(__name__)

_ALLOWED = re.compile(r"^\s*(SELECT|INSERT|UPDATE|DELETE)\b", re.IGNORECASE)
_BLOCKED = re.compile(r"\b(DROP|CREATE|ALTER|TRUNCATE|ATTACH|DETACH)\b", re.IGNORECASE)

SCHEMA = {
    "type": "function",
    "function": {
        "name": "execute_sql",
        "description": (
            "מריץ שאילתת SQL על ה-DB לניהול watchlist והתראות. "
            "מותר: SELECT, INSERT, UPDATE, DELETE. "
            "אסור: DROP, CREATE, ALTER."
        ),
        "parameters": {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "שאילתת SQL להרצה",
                }
            },
            "required": ["query"],
        },
    },
}


def handler(query: str) -> dict:
    if not _ALLOWED.match(query):
        return {"error": "מותרות רק שאילתות SELECT, INSERT, UPDATE, DELETE"}
    if _BLOCKED.search(query):
        return {"error": "שאילתה מכילה פקודה אסורה (DROP/CREATE/ALTER)"}

    try:
        cursor = execute(query)
        if query.strip().upper().startswith("SELECT"):
            rows = cursor.fetchall()
            return {"rows": [dict(row) for row in rows], "count": len(rows)}
        else:
            commit()
            return {"affected_rows": cursor.rowcount}
    except Exception as e:
        logger.error("execute_sql failed: %s | query: %s", e, query)
        return {"error": str(e)}
