from agent import run_agent
from fake_llm import FakeClient, text_reply, tool_reply
from tools import calculator, run_tool


def test_calculator_is_safe_and_correct():
    assert calculator("(2 + 3) * 4 ** 2") == "80"
    out, is_error = run_tool("calculator", {"expression": "__import__('os').system('rm -rf /')"})
    assert is_error and "not allowed" in out


def test_bad_arguments_become_tool_errors():
    out, is_error = run_tool("get_time", {"tz": "Asia/Tokyo"})      # wrong field name
    assert is_error and "timezone" in out


def test_agent_loop_runs_tool_then_answers():
    fake = FakeClient([tool_reply("calculator", {"expression": "6 * 7"}), text_reply("The answer is 42.")])
    assert run_agent(fake, "what is 6 times 7?", verbose=False, web_search=False) == "The answer is 42."
    history = fake.calls[1]["messages"]       # [user question, assistant tool_use, user tool_result, assistant answer]
    result = history[2]["content"][0]
    assert result["type"] == "tool_result" and result["content"] == "42"


def test_agent_stops_after_max_steps():
    fake = FakeClient([tool_reply("calculator", {"expression": "1+1"}) for _ in range(10)])
    assert "maximum" in run_agent(fake, "loop forever", max_steps=3, verbose=False, web_search=False)
