import asyncio
import logging
from telegram import Update
from telegram.ext import Application, CommandHandler, MessageHandler, ContextTypes, filters
from src.agent.agent import PriliAgent
from src.db import database as db
from src.config.settings import DAILY_DIGEST_HOUR, DAILY_DIGEST_MINUTE, TIMEZONE

logger = logging.getLogger(__name__)

_agent: PriliAgent | None = None


# ------------------------------------------------------------------
# Commands
# ------------------------------------------------------------------

async def start_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user = update.effective_user
    _register_user(user.id, user.username, user.first_name)
    await update.message.reply_text(
        f"שלום {user.first_name}! 👋\n"
        "אני PriliBot — העוזר האישי שלך לכלכלה והשקעות.\n\n"
        "אני יכול לעזור לך עם:\n"
        "• מחירי מניות ונתוני שוק בזמן אמת\n"
        "• חדשות כלכלה עדכניות\n"
        "• ניהול רשימת מעקב אחר מניות\n"
        "• התראות על שינויי מחיר\n"
        "• סקירה יומית בשעה 08:00\n\n"
        "פשוט כתוב לי מה אתה רוצה לדעת!"
    )


async def help_command(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    await update.message.reply_text(
        "מה אני יכול לעשות עבורך:\n\n"
        "📈 *מניות ושוק*\n"
        "• \"מה המחיר של AAPL?\"\n"
        "• \"איך נסחרת טבע היום?\"\n\n"
        "📰 *חדשות*\n"
        "• \"מה החדשות בשוק ההון היום?\"\n"
        "• \"יש חדשות על אנבידיה?\"\n\n"
        "📋 *רשימת מעקב*\n"
        "• \"תוסיף MSFT לרשימת המעקב שלי\"\n"
        "• \"מה יש ברשימת המעקב שלי?\"\n\n"
        "🔔 *התראות*\n"
        "• \"תתריע לי אם AAPL עולה מעל 200\"\n"
        "• \"תתריע לי אם TEVA יורדת מתחת ל-15\"\n\n"
        "💬 *שיחה חופשית*\n"
        "• כל שאלה על כלכלה, מניות והשקעות",
        parse_mode="Markdown"
    )


# ------------------------------------------------------------------
# Message handler
# ------------------------------------------------------------------

async def message_handler(update: Update, context: ContextTypes.DEFAULT_TYPE) -> None:
    user_id = update.effective_user.id
    text = update.message.text

    await context.bot.send_chat_action(chat_id=update.effective_chat.id, action="typing")

    try:
        response = await asyncio.to_thread(_agent.process_message, user_id, text)
    except Exception as e:
        logger.error("Agent error for user %d: %s", user_id, e)
        response = "מצטער, אירעה שגיאה. אנא נסה שוב."

    await update.message.reply_text(response)


# ------------------------------------------------------------------
# Daily digest job (placeholder — implemented in Stage 5)
# ------------------------------------------------------------------

async def daily_digest_job(context: ContextTypes.DEFAULT_TYPE) -> None:
    logger.info("Daily digest job triggered")
    # Implemented in Stage 5


# ------------------------------------------------------------------
# Setup
# ------------------------------------------------------------------

def setup(app: Application, agent: PriliAgent) -> None:
    global _agent
    _agent = agent

    app.add_handler(CommandHandler("start", start_command))
    app.add_handler(CommandHandler("help", help_command))
    app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, message_handler))

    app.job_queue.run_daily(
        daily_digest_job,
        time=_make_digest_time(),
        name="daily_digest",
    )
    logger.info("Bot handlers and daily job registered")


def _make_digest_time():
    import datetime
    import pytz
    tz = pytz.timezone(TIMEZONE)
    return datetime.time(hour=DAILY_DIGEST_HOUR, minute=DAILY_DIGEST_MINUTE, tzinfo=tz)


# ------------------------------------------------------------------
# Internal
# ------------------------------------------------------------------

def _register_user(telegram_id: int, username: str | None, first_name: str | None) -> None:
    try:
        db.execute(
            "INSERT OR IGNORE INTO users (telegram_id, username, first_name) VALUES (?, ?, ?)",
            (telegram_id, username, first_name),
        )
        db.commit()
    except Exception as e:
        logger.error("Failed to register user %d: %s", telegram_id, e)
