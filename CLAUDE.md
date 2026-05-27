# PriliBot

עוזר אישי ב-Telegram לתחום הכלכלה והשקעות — **משתמש יחיד** (הבעלים בלבד). ארבע יכולות מרכזיות:

1. **סקירת חדשות יומית** — תקציר יומי של חדשות כלכלה ושוק ההון
2. **המלצות מניות** — ניתוח והמלצות לפי קריטריונים שהמשתמש מגדיר מראש
3. **התראות פרואקטיביות** — push לפי הגדרות המשתמש (אירועים, סף מחיר, חדשות רלוונטיות)
4. **שיחה חופשית** — שאלות ותשובות בעברית על כלכלה, מניות והשקעות

## Bash Commands

```bash
pip install -r requirements.txt   # התקנה
python main.py                     # הרצה
pytest tests/                      # בדיקות
pytest tests/ -x -q                # בדיקות — עצור בכישלון ראשון
```

## Architecture

```
main.py
src/
  bot/handler.py              # Telegram handlers + daily job setup (setup())
  agent/agent.py              # agent loop + generate_daily_digest() — משתמש ב-Groq API
  services/
    stocks.py                 # yfinance — מחירים ומדדים
    news.py                   # Google News RSS + yfinance news
  tools/
    get_stock_data.py         # הבוט שואל על מניה ספציפית
    get_news.py               # הבוט מביא חדשות לפי נושא/ticker
    execute_sql.py            # הבוט מנהל DB (watchlist, התראות)
    get_schema.py             # הבוט רואה את מבנה ה-DB
    save_memory.py            # זיכרון ארוך-טווח → markdown
    search_memory.py          # חיפוש בזיכרון
  db/database.py              # SQLite singleton, WAL, thread lock, init_db()
  config/settings.py
data/
  prilibot.db                 # נוצר אוטומטית — users + כל מה שהבוט יוצר
  memory/YYYY-MM-DD.md        # זיכרון אפיזודי (קריטריונים, העדפות)
```

**Stack:** Python 3.11 + python-telegram-bot[job-queue] + Groq API (LLaMA 3.3 70B, חינם) + SQLite + yfinance + feedparser

**Deployment:** VPS (ענן) — הבוט רץ 24/7, לא תלוי במחשב המשתמש

**Data flows:**
```
שיחה חופשית:
  Telegram → handler.py → asyncio.to_thread → agent.process_message()
    → Groq (LLaMA 3.3 70B) בוחר tools → תשובה בעברית

סקירה יומית (08:00 ישראל):
  job_queue.run_daily → daily_digest_job()
    → stocks.get_market_summary() + news.get_financial_news_*()
      → agent.generate_daily_digest() → push לכל המשתמשים
```

**שכבות זיכרון:**
| שכבה | מיקום | שימוש |
|---|---|---|
| Short-term | `_sessions` dict ב-RAM | הקשר שיחה נוכחית (40 הודעות) |
| Structured | `data/prilibot.db` | watchlist, התראות, היסטוריה |
| Episodic | `data/memory/*.md` | קריטריונים, העדפות, מידע אישי |

## Language

- **כל תקשורת עם המשתמש היא בעברית בלבד** — תשובות, התראות, סקירה יומית, הודעות שגיאה
- ה-system prompt של הבוט חייב לכלול: "אתה עוזר אישי לכלכלה והשקעות. ענה תמיד בעברית בלבד, גם אם המשתמש כותב באנגלית."
- קוד, משתנים, לוגים — אנגלית (כמקובל)
- תיעוד קוד פנימי (comments) — אנגלית

## Code Style

- Python 3.11+, type hints בכל פונקציה
- async רק ב-handler.py — שאר הקוד synchronous
- שגיאות מוחזרות כ-`{"error": str}` — לא raise
- env vars נטענים רק דרך `settings.py`

## Gotchas

- `python-telegram-bot[job-queue]` חובה — job-queue לא כלול בגרסה הרגילה
- yfinance: מניות ישראליות מסתיימות ב-`.TA` (לדוגמה `TEVA.TA`), ת"א 35 = `TA35.TA`
- `asyncio.to_thread` משמש לכל קריאה blocking (Groq API, yfinance, feedparser)
- היסטוריית שיחה ב-RAM בלבד — מתאפסת עם restart
- **משתמש יחיד** — אין צורך ב-rate limiting, multi-user protection, או הגנה על נתוני משתמשים
- **Groq rate limits (free tier):** ~30 req/min, ~14,400 req/day — מספיק בנוחות למשתמש יחיד
- **LLM provider:** Groq API — `pip install groq`. מפתח ב-`GROQ_API_KEY`
- **Function calling:** Groq תומך ב-tool use עם LLaMA 3.3 70B — מבנה זהה ל-OpenAI

## Notes for Claude
1. "Before writing any code, describe your approach and wait for approval. Always ask clarifying questions before writing any code if requirements are ambiguous."

2. "If a task requires changes to more than 3 files, stop and break it into smaller tasks first."

3. "After writing code, list what could break and suggest tests to cover it."

4. "When there's a bug, start by writing a test that reproduces it, then fix it until the test passes."

5. "Every time I correct you, add a new rule to the CLAUDE .md file so it never happens again."

6. "Every meaningful change must be committed to git with a clear message. After completing each development stage, push to GitHub. Never leave working code uncommitted."