# 7.4 · AI agent with tools: calculator, weather, time, web search

**What you'll build:** an **agent**: an LLM in a loop that decides by itself which tools to call (a safe calculator, live weather, a world clock, and Claude's built-in **web search**), reads the results, and keeps going until it can answer. You write the loop yourself, so nothing is magic.
**Like you're 10:** a smart kid with a backpack of gadgets (calculator, thermometer, phone to look things up). For each question they decide which gadget to pull out, use it, look at the result, maybe use another gadget, and only then answer.
**Time:** ~2 h · **Builds on:** [7.3 RAG](../03-rag-ask-questions-about-your-pdfs) and [1.8 Weather proxy](../../level-1-apis/08-weather-proxy-calling-other-apis) · **Needs:** an Anthropic API key (tests run without one), internet

## Why this matters
On their own, models can't check today's weather, do exact maths on big numbers, or read your database. **Tool use** connects them to the real world, and it powers coding assistants, booking bots, data analysts and every "AI agent" product. The loop you write here (ask → run tools → send results → repeat) is the same one inside every agent framework, so after this lesson those frameworks stop being black boxes. Level 8 builds whole teams of agents on top of it.

## What you'll learn
- **Tool definition**: a name, a description and a JSON schema for the inputs. The description is a prompt: it tells the model *when* to use the tool.
- **The agent loop**: keep calling the model while it asks for tools (`stop_reason == "tool_use"`), and stop when it gives a final answer.
- **Client tools vs. server tools**: your functions run on your machine; `web_search` runs on Anthropic's servers.
- **Validating tool input and returning errors**: check the model's arguments with Pydantic and send mistakes back (`is_error: True`) so it can fix them.
- **Safety limits**: no `eval()` on model output, and a `max_steps` cap so an agent can't loop forever.

## Before you start
```bash
cd level-7-real-world-ai-apps/04-ai-agent-with-tools-calculator-weather-search
pip install -r requirements.txt
```
- `anthropic`: calls Claude. `httpx`: calls the free Open-Meteo weather API (no key needed).
- `pydantic`: describes and validates each tool's inputs.
- `tzdata`: the world's timezone database, needed by `get_time` on Windows (harmless elsewhere).
- `pytest`: tests.

**API key:** set `ANTHROPIC_API_KEY` as in the [Level 7 README](../README.md#api-key-needed-from-here-on). Web search is billed by Anthropic per search (a cent or so per question here); no extra key needed.

## Run it
1. From the course root: `cd level-7-real-world-ai-apps/04-ai-agent-with-tools-calculator-weather-search`
2. Tests (offline): `pytest -v`
3. Run the 3 built-in questions: `python agent.py`
4. Ask your own: `python agent.py "If I save 15% of a 3,200 monthly salary, how long until I have 10,000? Also what's the weather in Mumbai?"`

### What you should see
(Live data and wording will differ; the shape is what matters.)
```
❓ What is (1234 * 5678) - 99, and what time is it in Tokyo?
  🔧 step 1: calculator({"expression": "1234 * 5678 - 99"}) -> 7006553
  🔧 step 1: get_time({"timezone": "Asia/Tokyo"}) -> Thursday 15 October 2026, 13:25 (JST)
💬 (1234 × 5678) − 99 = 7,006,553, and it's 13:25 on Thursday in Tokyo.

❓ Is it warmer in Rome or Oslo right now? By how many degrees?
  🔧 step 1: get_weather({"city": "Rome"}) -> Rome, Italy: 21.4°C, wind 7.2 km/h
  🔧 step 1: get_weather({"city": "Oslo"}) -> Oslo, Norway: 9.8°C, wind 14.0 km/h
  🔧 step 2: calculator({"expression": "21.4 - 9.8"}) -> 11.6
💬 Rome is warmer: 21.4°C vs 9.8°C in Oslo, a difference of 11.6 degrees.

❓ Who won the most recent FIFA World Cup, and how many years ago was it?
  🌐 step 1: web_search({"query": "most recent FIFA World Cup winner"})
  🔧 step 2: calculator({"expression": "2026 - 2022"}) -> 4
💬 Argentina won the most recent FIFA World Cup (2022), which was 4 years ago.
```
What to look at:
- **Two 🔧 lines with the same step number** = a *parallel* tool call: the model asked for both at once.
- In question 2 the model **chained** tools: first two weather lookups, then the calculator on their results.
- **🌐** marks a server tool: Anthropic ran the search and sent back results; your code didn't run anything.

## How it works
```
question ─► Claude (+ tool definitions) ──"use calculator(1234*5678-99)"──► run_tool() on YOUR machine
              ▲                                                               │
              └──────────── tool_result "7006553" (in a user message) ◄───────┘
           ... repeat until stop_reason is not "tool_use" ... ─► final answer
```

### `tools.py`
1. **Input models.** `CalculatorInput`, `WeatherInput` and `TimeInput` are Pydantic classes. Their docstring becomes the tool's description and each `Field(description=...)` explains an argument. This is what Claude reads to decide when and how to call each tool.
2. **`calculator(expression)`** never uses `eval()` (which would run *any* Python the model wrote, e.g. deleting files). Instead `ast.parse` turns the text into a syntax tree and `ev()` walks it, allowing only numbers and the operators in `_OPS`. Huge exponents are refused, and float noise is rounded (`11.599999999999998` → `11.6`).
3. **`get_weather(city)`** calls Open-Meteo twice: the geocoding API turns "Rome" into latitude/longitude, then the forecast API returns the current temperature and wind. **`get_time(timezone)`** uses Python's `zoneinfo`.
4. **`REGISTRY`** maps each tool name to `(function, input model)`. **`tool_definitions()`** builds the list sent to Claude from it: name, description and the JSON schema from `model_json_schema()`. It also adds the server tool `web_search` with `max_uses: 3` (a cost cap), choosing the newest version for Opus/Sonnet and the basic version for Haiku.
5. **`run_tool(name, args)`** looks up the tool, validates the arguments with the Pydantic model (a wrong field name fails here, before anything runs), calls the function, and returns `(text, is_error)`. Any exception becomes an error message for the model instead of crashing your program.

### `agent.py`
1. **`messages`** starts with your question; **`tools`** comes from `tool_definitions()`.
2. **Each step** calls `llm.create(..., tools=tools, messages=messages)` and appends the *whole* `response.content` to `messages` as an assistant turn: text, tool calls, thinking and search results all have to go back so the model sees its own history.
3. **`pause_turn`**: a long server-side search can pause; sending the conversation back as-is lets it continue.
4. **Not `tool_use`** means the model is done, so `llm.text_of(response)` returns the final answer.
5. **Otherwise** every `tool_use` block is run with `run_tool()`, and each result becomes a `{"type": "tool_result", "tool_use_id": ..., "content": ..., "is_error": ...}` block. All of them go back in **one** user message (sending them one per message teaches the model to stop calling tools in parallel).
6. **`max_steps=8`** ends the loop with "Stopped: reached the maximum number of steps." if the model keeps asking for tools. Always cap agents: every step costs money.

### `test_agent.py`
Checks the calculator is correct and blocks an injection attempt, that bad arguments become tool errors, that the loop runs a tool then answers (using `fake_llm.tool_reply`), that `max_steps` stops a runaway loop, the weather formatting (with `httpx.get` replaced by a fake), and the web-search version choice. All offline.

## If something goes wrong
- **`anthropic.AuthenticationError`** → set `ANTHROPIC_API_KEY` in this terminal.
- **`get_time` returns `ZoneInfoNotFoundError` on Windows** → install the timezone data: `pip install tzdata` (it's in `requirements.txt`).
- **Weather answers say `ConnectError` or `ReadTimeout`** → Open-Meteo couldn't be reached (no internet, firewall or a temporary outage). The error went back to the model, which is why it explains instead of crashing. Try again later.
- **An error mentioning `web_search`** → your account or model may not allow web search. Run without it: change `run_agent(client, q)` in `agent.py` to `run_agent(client, q, web_search=False)`.
- **"Stopped: reached the maximum number of steps."** → the question needed more tool calls than allowed, or the model got stuck retrying a failing tool. Read the 🔧 lines to see which, then raise `max_steps` or fix the tool.

## Try this
1. **A note-taking tool.** Add `save_note(text)` that appends a line to `notes.txt`, then ask: "Find the population of Canada and save a one-line note about it."
   <details><summary>Solution</summary>

   In `tools.py`:
   ```python
   class NoteInput(BaseModel):
       """Save a short note to the user's notes file. Use it when the user asks you to remember or save something."""
       text: str = Field(description="The note, one or two sentences")


   def save_note(text: str) -> str:
       with open("notes.txt", "a", encoding="utf-8") as f:
           f.write(text.strip() + "\n")
       return "Saved."
   ```
   and add `"save_note": (save_note, NoteInput)` to `REGISTRY`. The loop needs no change: that's the beauty of the registry.
   </details>
2. **Count the cost.** Add up `response.usage.input_tokens` and `output_tokens` over all steps and print them (and the price) after each answer.
   <details><summary>Solution</summary>

   In `run_agent`, before the loop: `used = {"in": 0, "out": 0}`; right after `llm.create(...)`: `used["in"] += response.usage.input_tokens; used["out"] += response.usage.output_tokens`. Before `return llm.text_of(response)`, add
   ```python
   if verbose:
       cost = used["in"] / 1e6 * 4 + used["out"] / 1e6 * 20       # Claude Opus 5.5 prices per million tokens
       print(f"  💰 {used['in']} in / {used['out']} out tokens ≈ ${cost:.4f}")
   ```
   Notice that input tokens grow each step: the whole conversation, including tool results, is resent every time.
   </details>
3. **Currency conversion.** Add `convert_currency(amount, from_currency, to_currency)` using a free exchange-rate API, then ask "How much is 250 euros in Indian rupees?".
   <details><summary>Hint</summary>

   Search for a free, no-key exchange-rates API (the "Frankfurter" API is a popular one). Copy the shape of `get_weather`: one `httpx.get(..., timeout=10)`, pick the number out of the JSON, return a sentence like `"250 EUR = 22,950.00 INR (rate 91.80)"`. Use a Pydantic `Field(description="3-letter ISO code like EUR")` so the model sends codes, not names, and add a test that fakes `httpx.get` like `test_weather_tool_formats_the_api_reply`.
   </details>

## Check yourself
1. How does the model "call" `get_weather` when it can't run code?
2. Why must all tool results from one step go back in a single user message?
3. Why does `run_tool` return errors to the model instead of raising them?
4. When would you *not* use an agent and just write a fixed sequence of steps instead?

<details><summary>Answers</summary>

1. It doesn't run anything. It replies with a `tool_use` block (tool name + JSON arguments) and `stop_reason: "tool_use"`. *Your* code runs the function and sends the result back.
2. That's how the API pairs each `tool_use` with its `tool_result`, and splitting them across messages teaches the model to stop making parallel calls (slower agents).
3. The model can often fix the problem itself (wrong timezone name, typo in a city), and your program keeps running instead of crashing on the first mistake.
4. When the steps are known in advance (e.g. always: extract → validate → save). A fixed workflow is cheaper, faster and more predictable. Use an agent only when the path depends on the question.
</details>

## Learn more (optional)
- Building effective agents (Anthropic): https://www.anthropic.com/engineering/building-effective-agents
- Tool use docs: https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview
- AI agents explained: https://www.youtube.com/results?search_query=llm+agents+tool+use+explained

## Next
→ [7.5 · Evaluate your RAG and chatbot](../05-evaluate-your-rag-and-chatbot)
