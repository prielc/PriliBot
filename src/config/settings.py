import os
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

# Paths
BASE_DIR = Path(__file__).resolve().parent.parent.parent
DATA_DIR = BASE_DIR / "data"
MEMORY_DIR = DATA_DIR / "memory"
DB_PATH = os.getenv("DB_PATH", str(DATA_DIR / "prilibot.db"))

# Telegram
TELEGRAM_BOT_TOKEN: str = os.getenv("TELEGRAM_BOT_TOKEN", "")

# Groq
GROQ_API_KEY: str = os.getenv("GROQ_API_KEY", "")
GROQ_MODEL: str = "llama-3.3-70b-versatile"

# Agent
MAX_HISTORY_MESSAGES: int = 40
SYSTEM_PROMPT: str = (
    "אתה PriliBot — עוזר אישי חכם לכלכלה והשקעות. "
    "ענה תמיד בעברית בלבד, גם אם המשתמש כותב באנגלית. "
    "אתה מסייע בניתוח מניות, סקירת חדשות שוק ההון, המלצות השקעה לפי קריטריונים אישיים, "
    "וניהול רשימת מעקב והתראות. "
    "היה תמציתי, מקצועי, ומדויק. "
    "כשאתה לא בטוח בנתון — אמור זאת במפורש."
)

# Daily digest
DAILY_DIGEST_HOUR: int = 8
DAILY_DIGEST_MINUTE: int = 0
TIMEZONE: str = "Asia/Jerusalem"

# Alerts polling interval (seconds)
ALERTS_POLL_INTERVAL: int = 300

# Logging
LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")
