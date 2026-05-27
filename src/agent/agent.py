import json
import logging
from groq import Groq
from src.config.settings import (
    GROQ_API_KEY,
    GROQ_MODEL,
    SYSTEM_PROMPT,
    MAX_HISTORY_MESSAGES,
)

logger = logging.getLogger(__name__)

MAX_TOOL_ITERATIONS = 5


class PriliAgent:
    def __init__(self) -> None:
        self._client = Groq(api_key=GROQ_API_KEY)
        self._sessions: dict[int, list[dict]] = {}
        self._tools: list[dict] = []  # populated in Stage 3
        self._tool_handlers: dict[str, callable] = {}

    # ------------------------------------------------------------------
    # Public API
    # ------------------------------------------------------------------

    def process_message(self, user_id: int, text: str) -> str:
        history = self._get_history(user_id)
        history.append({"role": "user", "content": text})

        response_text = self._run_loop(history)

        history.append({"role": "assistant", "content": response_text})
        self._trim_history(user_id)
        return response_text

    def generate_daily_digest(self) -> str:
        from src.services.stocks import get_market_summary
        from src.services.news import get_financial_news

        market = get_market_summary()
        news = get_financial_news(max_results=5)

        market_text = "\n".join(
            f"- {name}: {data.get('price', 'N/A')} ({data.get('change_pct', 'N/A')}%)"
            if "error" not in data else f"- {name}: לא זמין"
            for name, data in market.items()
        )
        news_text = "\n".join(
            f"- {a['title']} ({a['source']})" for a in news
        ) if news else "לא נמצאו חדשות"

        prompt = (
            f"סכם את המצב הכלכלי של הבוקר בעברית בצורה תמציתית ומקצועית.\n\n"
            f"מדדים:\n{market_text}\n\n"
            f"כותרות חדשות:\n{news_text}\n\n"
            "כתוב סקירת בוקר קצרה (3-5 משפטים) שמסכמת את המצב ומדגישה נקודות חשובות."
        )

        response = self._client.chat.completions.create(
            model=GROQ_MODEL,
            messages=[
                {"role": "system", "content": SYSTEM_PROMPT},
                {"role": "user", "content": prompt},
            ],
        )
        return response.choices[0].message.content or "לא הצלחתי להכין סקירה יומית."

    def clear_session(self, user_id: int) -> None:
        self._sessions.pop(user_id, None)

    # ------------------------------------------------------------------
    # Tool registration (called from tools package in Stage 3)
    # ------------------------------------------------------------------

    def register_tool(self, schema: dict, handler: callable) -> None:
        self._tools.append(schema)
        self._tool_handlers[schema["function"]["name"]] = handler

    # ------------------------------------------------------------------
    # Internal
    # ------------------------------------------------------------------

    def _get_history(self, user_id: int) -> list[dict]:
        if user_id not in self._sessions:
            self._sessions[user_id] = []
        return self._sessions[user_id]

    def _trim_history(self, user_id: int) -> None:
        history = self._sessions.get(user_id, [])
        if len(history) > MAX_HISTORY_MESSAGES:
            self._sessions[user_id] = history[-MAX_HISTORY_MESSAGES:]

    def _build_messages(self, history: list[dict]) -> list[dict]:
        return [{"role": "system", "content": SYSTEM_PROMPT}] + history

    def _run_loop(self, history: list[dict]) -> str:
        for iteration in range(MAX_TOOL_ITERATIONS):
            kwargs: dict = {"model": GROQ_MODEL, "messages": self._build_messages(history)}
            if self._tools:
                kwargs["tools"] = self._tools
                kwargs["tool_choice"] = "auto"

            response = self._client.chat.completions.create(**kwargs)
            message = response.choices[0].message

            # No tool calls — return the text response
            if not message.tool_calls:
                return message.content or ""

            # Execute each tool call and collect results
            history.append({"role": "assistant", "content": message.content, "tool_calls": [
                {"id": tc.id, "type": "function", "function": {"name": tc.function.name, "arguments": tc.function.arguments}}
                for tc in message.tool_calls
            ]})

            for tool_call in message.tool_calls:
                result = self._execute_tool(tool_call.function.name, tool_call.function.arguments)
                history.append({
                    "role": "tool",
                    "tool_call_id": tool_call.id,
                    "content": json.dumps(result, ensure_ascii=False),
                })

            logger.debug("Tool iteration %d/%d completed", iteration + 1, MAX_TOOL_ITERATIONS)

        logger.warning("Reached max tool iterations (%d)", MAX_TOOL_ITERATIONS)
        return "מצטער, לא הצלחתי להשלים את הפעולה. נסה שוב."

    def _execute_tool(self, name: str, arguments_json: str) -> dict:
        handler = self._tool_handlers.get(name)
        if handler is None:
            logger.error("Unknown tool: %s", name)
            return {"error": f"כלי לא מוכר: {name}"}
        try:
            args = json.loads(arguments_json)
            return handler(**args)
        except Exception as e:
            logger.error("Tool %s failed: %s", name, e)
            return {"error": str(e)}
