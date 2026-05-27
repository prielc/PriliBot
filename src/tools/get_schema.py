import logging
from src.db.database import get_connection

logger = logging.getLogger(__name__)

SCHEMA = {
    "type": "function",
    "function": {
        "name": "get_schema",
        "description": "מחזיר את מבנה הטבלאות ב-DB כדי שתוכל לכתוב SQL נכון.",
        "parameters": {"type": "object", "properties": {}, "required": []},
    },
}


def handler() -> dict:
    try:
        conn = get_connection()
        tables = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table' ORDER BY name"
        ).fetchall()

        schema: dict[str, list] = {}
        for (table_name,) in tables:
            cols = conn.execute(f"PRAGMA table_info({table_name})").fetchall()
            schema[table_name] = [
                {"name": col["name"], "type": col["type"], "not_null": bool(col["notnull"]), "pk": bool(col["pk"])}
                for col in cols
            ]

        return {"tables": schema}
    except Exception as e:
        logger.error("get_schema failed: %s", e)
        return {"error": str(e)}
