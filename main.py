import logging
from telegram.ext import Application
from src.config.settings import LOG_LEVEL, TELEGRAM_BOT_TOKEN
from src.db.database import init_db
from src.agent.agent import PriliAgent
from src.tools import register_all_tools
from src.bot.handler import setup

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=getattr(logging, LOG_LEVEL, logging.INFO),
)
logging.getLogger("httpx").setLevel(logging.WARNING)
logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("Starting PriliBot...")

    init_db()
    logger.info("Database ready")

    agent = PriliAgent()
    register_all_tools(agent)
    logger.info("Agent and tools ready")

    app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
    setup(app, agent)

    logger.info("PriliBot is running — polling for messages")
    app.run_polling(drop_pending_updates=True)


if __name__ == "__main__":
    main()
