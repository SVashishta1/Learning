# 8.6 · Build your own MCP server

**What you'll build:** an **MCP server**, a plug that lets *any* AI application use your tools and data. This one manages study flashcards (`add_note`, `search_notes`, `quiz_me`, `record_result`), plus a resource and a reusable prompt. You'll poke it with a raw MCP client, let Claude drive it from Python, and connect it to **Claude Code** or **Claude Desktop**.
**Like you're 10:** USB lets any keyboard work with any computer. **MCP (Model Context Protocol)** is USB for AI: write the "device" (your tools) once, and every AI app that speaks MCP can plug it in.
**Time:** ~2 h · **Builds on:** [8.5 Code review crew](../05-code-review-crew-parallel-reviewers) and tools from [7.4](../../level-7-real-world-ai-apps/04-ai-agent-with-tools-calculator-weather-search) · **Needs:** nothing for the server and demo client; an Anthropic API key for `claude_with_mcp.py`

## Why this matters
In 7.4 your tools only worked inside your own script. In real companies, many AI apps (Claude, IDE assistants, internal agents) need the same tools: the CRM, the ticket system, the database. MCP is the open standard for this: build one server, and every MCP-capable app can use it. Writing MCP servers is one of the most requested AI-integration skills right now, and it's surprisingly little code.

## What you'll learn
- **MCP server**: a small program that offers tools, resources and prompts to AI apps in a standard format.
- **Tools, resources, prompts**: actions the AI can take, read-only data it can load, and ready-made prompt templates users can pick.
- **Schemas from type hints**: the MCP SDK turns your Python function signature and docstring into the tool definition.
- **stdio transport**: the AI app starts your server as a child process and talks to it through stdin/stdout.
- **MCP client + tool runner**: connecting the server to Claude from Python, letting the SDK run the tool loop.

## Before you start
```bash
cd level-8-multi-agent-systems/06-build-your-own-mcp-server
pip install -r requirements.txt
```
- `mcp>=2`: the official MCP Python SDK, version 2. Its server class is `MCPServer` (older tutorials use the v1 name `FastMCP`).
- `anthropic[mcp]`: the Claude SDK plus its MCP helpers (`async_mcp_tool`).
- `pytest`: tests.

No API key needed for the server, the tests and `client_demo.py`. For `claude_with_mcp.py`, set `ANTHROPIC_API_KEY` as in the [Level 7 README](../../level-7-real-world-ai-apps/README.md#api-key-needed-from-here-on).

## Run it
1. From the course root: `cd level-8-multi-agent-systems/06-build-your-own-mcp-server`
2. Tests: `pytest -v`
3. See what an AI app sees (no AI involved): `python client_demo.py`
4. Let Claude use your server: `python claude_with_mcp.py "Add 3 flashcards about attention in transformers, then quiz me on one"`
5. Plug it into Claude Code (use the **full path to your venv's Python**, so it has `mcp` installed):
   ```bash
   claude mcp add study-notes -- /FULL/PATH/TO/venv/bin/python /FULL/PATH/TO/06-build-your-own-mcp-server/server.py
   ```
   Then in Claude Code: *"Use study-notes to quiz me on RAG"*. (Windows: the venv Python is `...\venv\Scripts\python.exe`.)
6. Or plug it into Claude Desktop: Settings → Developer → Edit Config, add the block below, and restart Claude Desktop. Your tools appear in the chat.
   ```json
   {
     "mcpServers": {
       "study-notes": {
         "command": "/FULL/PATH/TO/venv/bin/python",
         "args": ["/FULL/PATH/TO/06-build-your-own-mcp-server/server.py"]
       }
     }
   }
   ```

Running `python server.py` on its own prints nothing and waits: it's waiting for an AI app to talk to it over stdin. Press Ctrl+C to stop it.

### What you should see
`python client_demo.py` (real output):
```
TOOLS the server offers:
  - add_note: Save a study note as a question/answer flashcard under a topic (e.g. 'RAG', 'PyTorch').
  - search_notes: Find notes whose topic, question or answer contains the query words.
  - quiz_me: Pick a flashcard to quiz the user, favouring cards they got wrong before. Returns the question and the hidden answer.
  - record_result: Record whether the user answered a quiz card correctly (spaced repetition).

add_note -> Saved note #1 in 'RAG'.
quiz_me  -> {"id": 1, "question": "What does the R in RAG stand for?", "answer_for_grading_only": "Retrieval"}
resource notes://topics -> {"RAG": 1}
```
(Each run adds the demo card again, so the note number grows. Delete `notes.json` to start fresh.)

`python claude_with_mcp.py` (representative; Claude's wording varies):
```
I'll add the two flashcards.
  🔧 add_note({'topic': 'fine-tuning', 'question': 'What does LoRA train instead of the full weight matrix?', 'answer': 'Two small low-rank matrices A and B ...'})
  🔧 add_note({'topic': 'fine-tuning', 'question': "Why does LoRA's B matrix start at zero?", 'answer': 'So the adapted model starts out identical to the pretrained one.'})
  🔧 search_notes({'query': 'fine-tuning'})
Done! I added two LoRA flashcards under 'fine-tuning'. You now have 2 cards on that topic.
```
What to look at: the tool descriptions in the list are exactly the docstrings in `server.py`; `notes.json` appears next to `server.py` and keeps your cards between runs.

## How it works
```
AI app (Claude Code / Desktop / claude_with_mcp.py / client_demo.py)
   │ starts:  python server.py           (stdio transport)
   │ ──"initialize", "tools/list"──────────►  MCPServer("study-notes")
   │ ──"tools/call add_note {...}"─────────►    add_note() → notes.json
   │ ◄─────────── "Saved note #1" ──────────
```

### `server.py`
1. **`mcp = MCPServer("study-notes")`** creates the server. `NOTES_FILE` is `notes.json` next to the script; `_load()` / `_save()` read and write it as JSON.
2. **`@mcp.tool()`** turns a normal function into an MCP tool. The SDK reads the type hints (`topic: str`, `note_id: int`, `was_correct: bool`) to build the input schema and the docstring as the description. That's why good names and docstrings matter: they're the instructions the AI reads.
3. **The four tools.** `add_note` appends a card with counters `correct`/`wrong`. `search_notes` returns up to 10 cards containing any query word. `quiz_me` picks a card with `random.choices`, weighting cards you got wrong more heavily (simple spaced repetition), and returns the answer labelled "for grading only". `record_result` updates the counters.
4. **`@mcp.resource("notes://topics")`** is read-only data with an address (a URI). Apps can load it as context, here a count of cards per topic.
5. **`@mcp.prompt()`** `study_session(topic)` is a reusable prompt template that a user can pick from a menu in apps like Claude Desktop: it describes a 5-question quiz session using the tools.
6. **`mcp.run()`** starts the stdio transport: read requests from stdin, write answers to stdout.

### `client_demo.py`
Plays the role of an AI app without any AI: `stdio_client` starts `server.py` as a child process (`sys.executable` = the same Python you're running), `ClientSession.initialize()` does the MCP handshake, then it lists tools, calls `add_note` and `quiz_me`, and reads the `notes://topics` resource.

### `claude_with_mcp.py`
Connects the same way, converts every MCP tool with `async_mcp_tool(t, mcp_client)` into a tool the Anthropic SDK understands, and hands them to `client.beta.messages.tool_runner(...)`. The **tool runner** does the agent loop from 7.4 for you: call Claude, run the requested tools through MCP, send results back, repeat. `async for message in runner` prints each step.

### `test_server.py`
Points `NOTES_FILE` at a temporary folder and calls the tool functions directly (they're still normal Python functions), checking add → search → quiz → record → topics.

## If something goes wrong
- **`ModuleNotFoundError: No module named 'mcp'`** → install the requirements in your venv. In Claude Code/Desktop configs, use the full path of the **venv's** Python, not plain `python`.
- **`ImportError: cannot import name 'MCPServer'`** → you have the old v1 SDK. Run `pip install -U "mcp>=2"`. (In v1 the same class was `from mcp.server.fastmcp import FastMCP`.)
- **`python server.py` "hangs"** → that's normal: a stdio server waits for an app to talk to it. Use `client_demo.py` to test it.
- **The server doesn't show up in Claude Desktop** → check the JSON is valid (commas!), that both paths are absolute, then fully quit and restart the app. Claude Desktop's MCP logs (Settings → Developer) show the server's error.
- **`anthropic.AuthenticationError`** in `claude_with_mcp.py` → set `ANTHROPIC_API_KEY`.

## Try this
1. **Export to Anki.** Add a tool `export_anki()` that writes `anki.csv` (question, answer per row) you can import into the Anki flashcard app.
   <details><summary>Solution</summary>

   ```python
   import csv

   @mcp.tool()
   def export_anki() -> str:
       """Export all flashcards to anki.csv (question,answer) for importing into Anki."""
       path = NOTES_FILE.with_name("anki.csv")
       with open(path, "w", newline="", encoding="utf-8") as f:
           csv.writer(f).writerows((n["question"], n["answer"]) for n in _load())
       return f"Exported {len(_load())} cards to {path}"
   ```
   Restart the server (or re-run the client) and the new tool appears in the list automatically.
   </details>
2. **Wrap an earlier project.** Make an MCP server that exposes the RAG app from 7.3 as one tool, `ask_handbook(question)`, so Claude Desktop can answer from the handbook.
   <details><summary>Hint</summary>

   Create `handbook_server.py` in the 7.3 folder: build the index once at startup (`index = Index(Embedder()).build(str(Path(__file__).with_name("docs")))`), then a tool `ask_handbook(question: str) -> str` that returns the top 4 chunks from `index.search(question)` as text with their sources. Let the *calling* AI write the answer: the server only retrieves. Register it in Claude Desktop like `study-notes`.
   </details>
3. **Go remote with HTTP.** Run the server over HTTP so other machines can use it.
   <details><summary>Solution</summary>

   Change the last line to `mcp.run(transport="streamable-http", host="0.0.0.0", port=8000)` and start `python server.py`. The MCP endpoint is `http://<your-ip>:8000/mcp`. Connect Claude Code with `claude mcp add --transport http study-notes http://localhost:8000/mcp`. A remote server needs authentication before you expose it to the internet (the SDK supports OAuth; see its docs).
   </details>

## Check yourself
1. What problem does MCP solve compared with the tools you wrote in 7.4?
2. What's the difference between a tool and a resource?
3. Where does the tool's description that Claude reads come from?
4. Why does a stdio server print nothing when you run it yourself?

<details><summary>Answers</summary>

1. 7.4's tools only worked inside that one script. An MCP server is written once and works with any MCP app (Claude Code, Claude Desktop, IDEs, your own agents) without rewriting the tools for each.
2. A tool is an action the AI decides to call, possibly changing something (add a note). A resource is read-only data at an address that an app can load as context (the topic overview).
3. From the function's docstring, and the input schema from its type hints. `@mcp.tool()` reads both.
4. It's waiting for MCP messages on stdin, and stdout is reserved for MCP replies (printing random text there would corrupt the protocol).
</details>

## Learn more (optional)
- MCP docs and quickstart: https://modelcontextprotocol.io/
- MCP Python SDK (v2 `MCPServer`; older tutorials say `FastMCP`): https://github.com/modelcontextprotocol/python-sdk
- Connect Claude Code to MCP servers: https://docs.claude.com/en/docs/claude-code/mcp

## Next
→ [8.7 · Human-in-the-loop file organizer](../07-human-in-the-loop-file-organizer-agent)
