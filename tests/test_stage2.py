import os
import json
import pytest
from unittest.mock import MagicMock, patch

os.environ.setdefault("TELEGRAM_BOT_TOKEN", "test")
os.environ.setdefault("GROQ_API_KEY", "test")


def _make_agent():
    from src.agent.agent import PriliAgent
    return PriliAgent()


def _mock_groq_response(content: str, tool_calls=None):
    message = MagicMock()
    message.content = content
    message.tool_calls = tool_calls or []
    choice = MagicMock()
    choice.message = message
    response = MagicMock()
    response.choices = [choice]
    return response


# ------------------------------------------------------------------
# Session management
# ------------------------------------------------------------------

def test_new_user_gets_empty_session():
    agent = _make_agent()
    history = agent._get_history(42)
    assert history == []


def test_session_stores_messages():
    agent = _make_agent()
    agent._sessions[1] = [{"role": "user", "content": "שלום"}]
    assert len(agent._get_history(1)) == 1


def test_trim_history():
    agent = _make_agent()
    agent._sessions[1] = [{"role": "user", "content": str(i)} for i in range(50)]
    agent._trim_history(1)
    assert len(agent._sessions[1]) == 40


def test_clear_session():
    agent = _make_agent()
    agent._sessions[1] = [{"role": "user", "content": "x"}]
    agent.clear_session(1)
    assert 1 not in agent._sessions


# ------------------------------------------------------------------
# process_message — no tools
# ------------------------------------------------------------------

def test_process_message_returns_text():
    agent = _make_agent()
    with patch.object(agent._client.chat.completions, "create",
                      return_value=_mock_groq_response("שלום! אני PriliBot")):
        result = agent.process_message(1, "היי")
    assert result == "שלום! אני PriliBot"


def test_process_message_builds_history():
    agent = _make_agent()
    with patch.object(agent._client.chat.completions, "create",
                      return_value=_mock_groq_response("תשובה")):
        agent.process_message(1, "שאלה")
    history = agent._get_history(1)
    assert history[0]["role"] == "user"
    assert history[1]["role"] == "assistant"


# ------------------------------------------------------------------
# Tool registration and execution
# ------------------------------------------------------------------

def test_register_tool():
    agent = _make_agent()
    schema = {"function": {"name": "test_tool"}, "type": "function"}
    handler = lambda: {"ok": True}
    agent.register_tool(schema, handler)
    assert "test_tool" in agent._tool_handlers
    assert len(agent._tools) == 1


def test_execute_unknown_tool_returns_error():
    agent = _make_agent()
    result = agent._execute_tool("nonexistent", "{}")
    assert "error" in result


def test_tool_loop_calls_handler():
    agent = _make_agent()

    schema = {"type": "function", "function": {"name": "get_price", "parameters": {}}}
    handler = MagicMock(return_value={"price": 150})
    agent.register_tool(schema, handler)

    tool_call = MagicMock()
    tool_call.id = "call_1"
    tool_call.function.name = "get_price"
    tool_call.function.arguments = "{}"

    with patch.object(agent._client.chat.completions, "create", side_effect=[
        _mock_groq_response("", tool_calls=[tool_call]),
        _mock_groq_response("המחיר הוא 150"),
    ]):
        result = agent.process_message(1, "מה המחיר?")

    handler.assert_called_once()
    assert result == "המחיר הוא 150"
