# Part 4 · Chatbots

Now you talk to a real AI (**Claude**) from your own code, then build chatbots with memory, a personality, a database and a web page.

| # | Project | What you'll have |
|---|---------|------------------|
| 16 | [Your first message to an AI](16-your-first-message-to-an-ai) | Claude answering from your code |
| 17 | [Chatbot with memory](17-chatbot-with-memory) | a terminal chatbot that remembers the conversation |
| 18 | [Chatbot API that saves chats](18-chatbot-api-that-saves-chats) | a chatbot behind an API, chats stored in a database |
| 19 | [Chatbot with a web page](19-chatbot-with-a-web-page) | your own mini ChatGPT in the browser |
| 20 | [AI turns messy text into data](20-ai-turns-messy-text-into-data) | receipts and emails → clean tables |

## Get your API key (once, about 5 minutes)
1. Go to https://platform.claude.com and sign up.
2. Add a small amount of credit ($5 is plenty for this whole course).
3. Create an API key and copy it (it starts with `sk-ant-`). **Treat it like a password.** Never share it or put it in a file you upload.
4. In your terminal (every time you open a new one):
   ```bash
   # Mac
   export ANTHROPIC_API_KEY=sk-ant-your-key-here
   # Windows PowerShell
   $env:ANTHROPIC_API_KEY="sk-ant-your-key-here"
   ```
5. Optional, but recommended while learning (cheapest and fastest model):
   ```bash
   export CLAUDE_MODEL=claude-haiku-5-5          # Mac
   $env:CLAUDE_MODEL="claude-haiku-5-5"          # Windows
   ```

Install once:
```bash
pip install anthropic fastapi "uvicorn[standard]" pydantic
```

Every project has the same small helper file, **`ai.py`**. It hides the boring details so your project code stays short. Its main function is `ask(messages)`, which sends a conversation to Claude and returns the reply.
