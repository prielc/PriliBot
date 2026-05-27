import logging
from src.config.settings import LOG_LEVEL
from src.db.database import init_db

logging.basicConfig(
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    level=getattr(logging, LOG_LEVEL, logging.INFO),
)
logger = logging.getLogger(__name__)


def main() -> None:
    logger.info("Starting PriliBot...")
    init_db()
    logger.info("Database ready")
    # Bot startup will be added in Stage 2
    logger.info("PriliBot is running")


if __name__ == "__main__":
    main()
