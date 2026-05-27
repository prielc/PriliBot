import logging
from datetime import date
from src.config.settings import MEMORY_DIR

logger = logging.getLogger(__name__)

SCHEMA = {
    "type": "function",
    "function": {
        "name": "save_memory",
        "description": "שומר מידע חשוב לזיכרון ארוך-טווח (העדפות, קריטריונים, מידע אישי) שיהיה זמין בשיחות עתידיות.",
        "parameters": {
            "type": "object",
            "properties": {
                "content": {
                    "type": "string",
                    "description": "המידע לשמירה",
                }
            },
            "required": ["content"],
        },
    },
}


def handler(content: str) -> dict:
    try:
        MEMORY_DIR.mkdir(parents=True, exist_ok=True)
        today = date.today().isoformat()
        memory_file = MEMORY_DIR / f"{today}.md"

        with open(memory_file, "a", encoding="utf-8") as f:
            f.write(f"\n- {content}\n")

        return {"saved": True, "file": str(memory_file)}
    except Exception as e:
        logger.error("save_memory failed: %s", e)
        return {"error": str(e)}
