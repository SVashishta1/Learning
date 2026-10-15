# 28 · Agent with many tools

**What you'll build:** an assistant with a calculator, live weather, world clocks, a note-saver and **web search**. For each question it chooses which tools to use, and in what order, by itself.
**Time:** ~1 hour · **Builds on:** [27 · AI uses a calculator](../27-ai-uses-a-calculator) · **Needs:** an Anthropic API key and an internet connection

## Why this matters
Real assistants have many tools, and nobody writes "if the question mentions weather, call the weather function". The AI reads the tool descriptions and plans by itself. This lesson also introduces `agent.py`, a small reusable agent engine: the same loop as lesson 27, written once, used by every project until the end of the course.

## What you'll learn
- **Tool selection:** the AI picks the right tools (and the order) from their descriptions alone.
- **Agent engine (`agent.py`):** `tool(...)` describes a function in one line, and `run_agent(...)` runs the ask → tool → result loop for you.
- **Server tools:** web search is a tool that Anthropic runs for you; you just switch it on.
- **Calling a real web API from a tool:** `get_weather` asks a free weather service over the internet.
- **Errors as information:** when a tool fails, the error text goes back to the AI so it can try again or explain.

## Before you start
- Install the Part 6 packages (once):
  ```bash
  pip install anthropic chromadb pypdf fastapi "uvicorn[standard]" python-multipart httpx tzdata
  ```
  Used here: `anthropic` (Claude), `httpx` (calls the free Open-Meteo weather service, no key needed), `tzdata` (time zone data; Windows needs it for `get_time`).
- Set your API key in this terminal (full steps in the [Part 4 README](../../part-4-chatbots)):
  ```bash
  export ANTHROPIC_API_KEY=sk-ant-your-key-here        # Mac
  $env:ANTHROPIC_API_KEY="sk-ant-your-key-here"        # Windows PowerShell
  ```
- Web search costs a little extra per search (a cent or so). The agent is limited to 3 searches per question.

## Run it
1. From the course folder (`Learning/ai-from-zero`), with your venv switched on:
   ```bash
   cd part-6-ai-agents-and-teams/28-agent-with-many-tools
   python assistant.py
   ```
2. Ask your own question:
   ```bash
   python assistant.py "What time is it in Tokyo, and how many hours ahead of London is that?"
   ```
3. Open `notes.txt` (it appears in this folder) to see what the agent saved.

### What you should see
For the default question ("Is it warmer in Rome or Oslo right now, and by how many degrees? Also find one interesting AI news story from this week and save it as a note."):
```
   🔧 Agent used get_weather({"city": "Rome"}) → Rome: 21.4°C
   🔧 Agent used get_weather({"city": "Oslo"}) → Oslo: 8.9°C
   🔧 Agent used calculate({"expression": "21.4 - 8.9"}) → 12.5
   🌐 Agent used web_search({"query": "AI news this week"})
   🔧 Agent used save_note({"text": "AI news: ... (source: https://...)"}) → Saved to notes.txt
Rome is warmer right now: 21.4°C versus 8.9°C in Oslo, a difference of 12.5 degrees.
I also found this week's AI story and saved it to notes.txt: ...
```
Your temperatures, news and wording will differ (it's live data). Look at the order: the AI fetched both temperatures *before* subtracting, and searched *before* saving the note. Nobody programmed that order. `🔧` lines are your Python tools; `🌐` lines are Anthropic's web search.

## How it works
**`agent.py`, the engine** (you'll reuse it in lessons 30–32):
1. `tool(function, description, inputs)` builds the tool description from lesson 27 for you. `inputs` is a small dictionary like `{"city": ("string", "City name")}`. The tool's name is taken from the function's name (`function.__name__`).
2. `WEB_SEARCH` switches on Claude's built-in web search. Haiku models get the basic version of the tool, the bigger models the newer one. `max_uses: 3` caps searches per question (and cost).
3. `run_agent(task, tools, ...)` is lesson 27's loop, with extras:
   - `by_name` maps tool names to your functions, so `by_name["get_time"](**block.input)` calls the right one.
   - Web search runs on Anthropic's side: its blocks have the type `server_tool_use`, and the engine just prints them with 🌐. If a long search pauses (`stop_reason == "pause_turn"`), the loop simply asks again to let it continue.
   - If your tool raises an error, `except Exception as error` sends `"Error: ..."` back to the AI instead of crashing.
   - `needs_approval`, `show` and `trace` are options used in later lessons (asking you before risky tools, staying quiet, collecting tool uses for a web page).
   - `max_steps=10` stops a confused agent from looping forever.

**`assistant.py`, the tools:**
1. `calculate(expression)`: the safe calculator from lesson 27.
2. `get_weather(city)`: two web requests to Open-Meteo, a free weather service. The first finds the city's latitude and longitude, the second gets the current temperature there. If the city isn't found it says so.
3. `get_time(timezone)`: `ZoneInfo("Asia/Tokyo")` knows each time zone's offset, and `strftime("%A %H:%M")` formats it like `Thursday 21:40`.
4. `save_note(text)`: opens `notes.txt` in `"a"` (append) mode, so each note is added to the end.
5. `tools = [tool(...), ...]` describes all four. The last line runs the agent with `web_search=True`.

## If something goes wrong
- **`ModuleNotFoundError: No module named 'httpx'`** → run the Part 6 `pip install` line inside your venv.
- **`🔧 ... get_time(...) → Error: 'No time zone found with key Asia/Tokyo'`** → your computer has no time zone data (common on Windows). Run `pip install tzdata`.
- **`get_weather` returns something like `Error: [Errno 8] nodename nor servname provided` or `Error: timed out`** → no internet connection, or a firewall blocks open-meteo.com. Check your connection; the rest of the agent still works.
- **`❌ ANTHROPIC_API_KEY is not set`** → set your key in this terminal.
- **An error mentioning `web_search`** (for example that the tool isn't available) → web search may need to be enabled for your organisation in the Claude Console (Settings), or your model doesn't support it. Try again without it by changing `web_search=True` to `web_search=False`.

## Try this
1. Write a new tool, `flip_coin()`, add it to `tools`, and ask `"Flip a coin 3 times and tell me how many heads."`.
   <details><summary>Solution</summary>

   ```python
   import random

   def flip_coin():
       return random.choice(["heads", "tails"])

   # add to the tools list:
   tool(flip_coin, "Flip a fair coin once. Returns heads or tails.", {}),
   ```
   `{}` means the tool takes no inputs. Watch: the AI calls it 3 times (maybe all at once).
   </details>
2. Ask a question that needs 3 different tools, for example `"What's the temperature in Paris in Fahrenheit, what time is it there, and save both in a note."`. Watch the order it picks.
   <details><summary>Hint</summary>

   It should call `get_weather` and `get_time` (they don't depend on each other, so possibly in the same step), then `calculate` for the Fahrenheit conversion (°C × 9 / 5 + 32), then `save_note` last, because the note needs the other results.
   </details>
3. Make the descriptions vague: change every description to `"does stuff"`. Ask the default question again. Does the agent still pick the right tools? Put them back afterwards.
   <details><summary>Hint</summary>

   It often still guesses from the function names (`get_weather` is a strong hint) but makes more mistakes, asks fewer tools or uses them wrongly (e.g. sends `"Rome weather"` to `calculate`). Rename `get_weather` to `tool_a` as well and it gets much worse. Lesson: good names and descriptions are part of your program.
   </details>

## Check yourself
1. Who decides which tools to use, and in which order?
2. What is the difference between `get_weather` and `web_search`, from your program's point of view?
3. What happens if `get_weather` crashes with an error?
4. Why does `run_agent` have a `max_steps` limit?

<details><summary>Answers</summary>

1. The AI, based on the question and the tool names and descriptions. Your code only provides the tools and runs them when asked.
2. `get_weather` is your Python function: your code runs it and sends the result back. `web_search` runs on Anthropic's servers: you only switch it on, and the results arrive inside Claude's reply.
3. `run_agent` catches it and sends `"Error: ..."` back as the tool result. The AI can then try again (e.g. a different city spelling) or explain the problem.
4. So a confused agent can't loop forever, using up time and money. After 10 rounds it stops with "Stopped: too many steps."
</details>

## Learn more (optional)
- [Claude docs: tool use overview](https://platform.claude.com/docs/en/agents-and-tools/tool-use/overview)
- [Open-Meteo](https://open-meteo.com/) (the free weather API used here)
- Video search: [AI agents explained](https://www.youtube.com/results?search_query=ai+agents+explained+tool+use)

## Next
→ [29 · Two AIs: writer and critic](../29-two-ais-writer-and-critic)
