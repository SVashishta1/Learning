# Part 4 · Chatbots

Now you talk to a real AI (**Claude**, made by Anthropic) from your own code, then build chatbots with memory, a personality, a database and a web page.

| # | Project | What you'll have | Time |
|---|---------|------------------|------|
| 16 | [Your first message to an AI](16-your-first-message-to-an-ai) | Claude answering from your code | 45 min |
| 17 | [Chatbot with memory](17-chatbot-with-memory) | a terminal chatbot that remembers the conversation | 45 min |
| 18 | [Chatbot API that saves chats](18-chatbot-api-that-saves-chats) | a chatbot behind an API, chats stored in a database | 1 hour |
| 19 | [Chatbot with a web page](19-chatbot-with-a-web-page) | your own mini ChatGPT in the browser | 1 hour |
| 20 | [AI turns messy text into data](20-ai-turns-messy-text-into-data) | receipts and emails → clean tables | 45 min |

Do **Get your API key** below first (about 10 minutes, once). Then do the projects in order.

## Get your API key (once, about 10 minutes)

An **API key** is a long secret password that lets your code use Claude. Anthropic uses it to know whose account to charge. It's pay-as-you-go: you buy a little credit up front and each message uses a tiny bit of it.

### Step 1: Make an account
1. Go to **https://console.anthropic.com** (it may send you on to `platform.claude.com`; that's the same place, Anthropic's developer console).
2. Click **Sign up** and use your email or Google account. Confirm your email if asked.
3. If it asks what you're using it for, any honest answer is fine (for example "personal learning").

This is separate from a Claude.ai chat subscription. A Claude Pro plan does **not** include API credit, and you don't need one.

### Step 2: Add credit
1. In the console, open **Settings → Billing** (sometimes shown as **Plans & Billing**).
2. Add a card and **buy credits**. The smallest amount (about **$5**) is plenty for this whole course.
3. Leave **auto-reload** turned **off**. Then you can never spend more than the credit you bought: when it runs out, requests simply stop working until you add more.

Some accounts get a small amount of free trial credit; if you have it, you can start with that.

### Step 3: Create the key
1. Open **Settings → API keys** (or the **API keys** item in the menu).
2. Click **Create key**, give it a name like `ai-from-zero`, and create it.
3. **Copy the key now.** It starts with `sk-ant-` and is shown only once. Paste it somewhere private for a minute (like a password manager). If you lose it, just delete it and create a new one.

**Treat the key like a password.** Anyone who has it can spend your credit.
- Never paste it into your code files, a screenshot, a chat, or a forum post.
- Never commit it to Git or upload it to GitHub. (Bots scan GitHub for leaked keys within minutes.)
- If it ever leaks, go to **API keys** in the console and **delete** it, then make a new one.

This course never asks you to put the key in a file. It reads the key from a setting in your terminal called an **environment variable**, named `ANTHROPIC_API_KEY`. That way there's no file with your key in it that you could upload by accident.

### Step 4: Give the key to your terminal
**Option A: just for this terminal window (simplest).** You'll redo this each time you open a new terminal.

| Your system | Type this (with your real key) |
|-------------|--------------------------------|
| Windows (PowerShell) | `$env:ANTHROPIC_API_KEY="sk-ant-your-key-here"` |
| Windows (Command Prompt) | `set ANTHROPIC_API_KEY=sk-ant-your-key-here` |
| Mac / Linux | `export ANTHROPIC_API_KEY=sk-ant-your-key-here` |

**Option B: remember it for every new terminal.**

| Your system | Type this once, then close and reopen the terminal |
|-------------|----------------------------------------------------|
| Windows | `setx ANTHROPIC_API_KEY "sk-ant-your-key-here"` |
| Mac (zsh, the default) | `echo 'export ANTHROPIC_API_KEY=sk-ant-your-key-here' >> ~/.zshrc` |
| Linux (bash) | `echo 'export ANTHROPIC_API_KEY=sk-ant-your-key-here' >> ~/.bashrc` |

Option B saves the key in a settings file in your home folder, outside this course folder, so it won't end up in Git. If you later need to change it, run the line again (Windows) or edit that file (Mac/Linux).

**Check it worked** (any system, venv on):
```bash
python -c "import os; print('key is set' if os.getenv('ANTHROPIC_API_KEY') else 'key is NOT set')"
```

### Step 5 (optional): choose a cheaper model while learning
The code uses **Claude Opus 5.5** (`claude-opus-5-5`, the most capable everyday model) unless you say otherwise. To use the cheapest and fastest model, **Claude Haiku 5.5**, set one more setting the same way as the key:

| Your system | This terminal only |
|-------------|--------------------|
| Windows (PowerShell) | `$env:CLAUDE_MODEL="claude-haiku-5-5"` |
| Mac / Linux | `export CLAUDE_MODEL=claude-haiku-5-5` |

You can also use `claude-sonnet-5-5` (in between). Type the model name exactly; a typo gives a "model not found" error.

### What does it cost?
You pay per **token** (a token is a piece of a word, roughly ¾ of a word). Prices per million tokens, as of October 2026:

| Model | Name in code | Input | Output | One short chat message (about) |
|-------|--------------|-------|--------|-------------------------------|
| Claude Haiku 5.5 | `claude-haiku-5-5` | $0.10 | $0.50 | well under 0.1 cent |
| Claude Sonnet 5.5 | `claude-sonnet-5-5` | $2 | $10 | about 0.3 cent |
| Claude Opus 5.5 | `claude-opus-5-5` | $4 | $20 | about 0.5–1 cent |

The whole of Part 4 typically costs well under $1 with Opus 5.5, and a few cents with Haiku 5.5. Long chats cost more per message, because the whole conversation is sent each time (project 17 explains why). You can see exactly what you've spent under **Usage** in the console. Prices change, so check the current ones at https://platform.claude.com/docs/en/about-claude/pricing.

## Install once
With your virtual environment on (see [00 · Start here](../00-start-here)), from the `ai-from-zero` folder:
```bash
pip install anthropic fastapi "uvicorn[standard]" pydantic
```
| Package | What it's for |
|---------|---------------|
| `anthropic` | Anthropic's official library for talking to Claude |
| `fastapi`, `uvicorn` | your web API from Part 1 (projects 18 and 19) |
| `pydantic` | describes the shape of data, like a form (projects 18–20) |

## The helper file: `ai.py`
Projects 17–20 (and Parts 5–6) each have the same small helper file, **`ai.py`**. It hides the boring details so your project code stays short:
- `ask(messages)` sends a conversation to Claude and returns the reply as text.
- `stream(messages)` does the same but gives you the reply piece by piece as it's written.
- `ask_for_data(text, Form)` makes Claude fill in a form (a Pydantic class) and gives you back a Python object.
- If your key is missing or wrong, it stops with a clear ❌ message instead of a wall of red text.
- On Opus 5.5 and Sonnet 5.5 it switches on a **safety net**: in the rare case Claude declines a request, Anthropic's servers automatically retry it on another model, so you still get an answer.

Project 16 does everything without the helper, so you see every part once.

## Common problems in Part 4
- **`❌ ANTHROPIC_API_KEY is not set in this terminal`** → do Step 4 in the terminal you're running the code in. A new terminal window forgets Option A.
- **`❌ Your API key is wrong or was deleted`** (or `AuthenticationError`, error 401) → copy the key again carefully (no spaces, no extra quotes inside), or create a new key.
- **`Your credit balance is too low to access the Anthropic API`** → add credit (Step 2). It can take a minute to start working.
- **`NotFoundError ... model`** (error 404) → `CLAUDE_MODEL` has a typo. Use exactly `claude-haiku-5-5`, `claude-sonnet-5-5` or `claude-opus-5-5`, or remove the setting.
- **`RateLimitError`** (error 429) or **`OverloadedError`** (error 529) → you sent many requests quickly, or Anthropic is busy. Wait a minute and try again.
