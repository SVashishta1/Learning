# 8.6 · Build your own MCP server

**What you build:** an **MCP server**, a plug that lets *any* AI application use your tools and data. This one manages study flashcards (`add_note`, `search_notes`, `quiz_me`, `record_result`), plus a resource and a reusable prompt. You'll connect it to **Claude Code** or **Claude Desktop**, poke it with a raw MCP client, and let Claude drive it from Python.
**Like you're 10:** USB lets any keyboard work with any computer. **MCP (Model Context Protocol)** is USB for AI: write the "device" (your tools) once, and every AI app that speaks MCP can plug it in.

## Run it
```bash
cd level-8-multi-agent-systems/06-build-your-own-mcp-server
pip install -r requirements.txt
python client_demo.py              # see what an AI app sees: tool list, a call, a resource (no API key needed)
export ANTHROPIC_API_KEY=sk-ant-...
python claude_with_mcp.py "Add 3 flashcards about attention in transformers, then quiz me on one"
```
Tests: `pytest -v`

## Plug it into Claude Code
```bash
claude mcp add study-notes -- python /FULL/PATH/TO/06-build-your-own-mcp-server/server.py
```
Then in Claude Code: *"Use study-notes to quiz me on RAG"*.

## Plug it into Claude Desktop
Settings → Developer → Edit Config, then add:
```json
{
  "mcpServers": {
    "study-notes": {
      "command": "python",
      "args": ["/FULL/PATH/TO/06-build-your-own-mcp-server/server.py"]
    }
  }
}
```
Restart Claude Desktop. Your tools now appear in the chat.

## Key ideas
| MCP concept | In this server | Meaning |
|-------------|----------------|---------|
| **Tool** | `@mcp.tool()` | an action the AI can take (add, search, quiz) |
| **Resource** | `@mcp.resource("notes://topics")` | read-only data the app can load as context |
| **Prompt** | `@mcp.prompt()` | a reusable prompt template users can pick |
| **Transport** | stdio | the app launches your server and talks over stdin/stdout (HTTP is also supported for remote servers) |

- Type hints and docstrings become the tool schema and description. Write them well!
- **Why companies care:** build one MCP server for your CRM, database or ticket system and every AI tool in the company can use it. MCP skills are in high demand.

## Your turn
1. Add `export_anki()`, which writes a CSV you can import into Anki.
2. Wrap one of your earlier projects as an MCP server: the RAG app from 7.3 (`ask_handbook(question)`) or the SQL analyst from 8.4.
3. Switch the transport to HTTP (`mcp.run(transport="streamable-http")`) and connect from another machine.

## Read
- MCP docs and quickstart: https://modelcontextprotocol.io/
- Python SDK (v2, `MCPServer`; older tutorials call it `FastMCP`): https://github.com/modelcontextprotocol/python-sdk
