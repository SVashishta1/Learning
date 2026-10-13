# 7.4 · AI agent with tools: calculator, weather, time, web search

**What you build:** an **agent**, an LLM in a loop that decides by itself which tools to call (a safe calculator, live weather, world clock, and Claude's built-in **web search**), reads the results, and keeps going until it can answer. You write the loop yourself, so nothing is magic.
**Like you're 10:** a smart kid with a backpack of gadgets (calculator, thermometer, phone to look things up). For each question they decide which gadget to pull out, use it, look at the result, maybe use another gadget, and only then answer.

## Run it
```bash
cd level-7-real-world-ai-apps/04-ai-agent-with-tools-calculator-weather-search
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
python agent.py
python agent.py "If I save 15% of a 3,200 monthly salary, how long until I have 10,000? Also what's the weather in Mumbai?"
```
You'll see each tool call printed (🔧) as the agent works.

Tests (offline): `pytest -v`

## The agent loop in 6 lines
```
messages = [question]
loop:
    response = claude(messages, tools)
    if response wants tools:  run them → append results → continue
    else:                     return the answer
```

## Key ideas
- **Tool definition = name + description + JSON schema.** The *description* is a prompt: good descriptions make agents good.
- **Client tools vs. server tools:** `calculator`, `get_weather` and `get_time` run on *your* machine; `web_search` runs on Anthropic's servers (no extra key).
- **Validate tool inputs** (Pydantic) and **return errors to the model** (`is_error: True`), so it can correct itself.
- **Safety:** the calculator parses the expression tree instead of calling `eval()`. Never execute model output blindly.
- **`max_steps`:** agents can loop; always cap steps (and cost).
- **Parallel tool calls:** the model may request several tools at once; we return *all* results in one message.

## Your turn
1. Add a `currency_convert(amount, from, to)` tool using a free rates API.
2. Add a `save_note(text)` tool that appends to `notes.txt`, then ask the agent to research something and save a summary.
3. Track tokens (`response.usage`) across steps and print the total cost of each question.

## Read / watch
- Building effective agents (Anthropic): https://www.anthropic.com/engineering/building-effective-agents
- Tool use docs: https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview
