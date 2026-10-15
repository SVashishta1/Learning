# 17 · Chatbot with memory

**What you'll build:** a chatbot in your terminal that remembers everything you've said, types its answers live, and can have any personality you give it.
**Time:** ~45 min · **Builds on:** [16 · Your first message to an AI](../16-your-first-message-to-an-ai) · **Needs:** an Anthropic API key (see the [Part 4 README](../README.md))

## Why this matters
Every chat product (ChatGPT, Claude.ai, support bots on websites) uses the trick in this project: the model forgets everything, so the app keeps the conversation and sends it again each turn. Understanding this explains why long chats get slower and more expensive, and why chatbots have a "context limit".

## What you'll learn
- **Conversation history as memory:** the AI remembers nothing, so your code keeps a list of every message and sends the whole list each time.
- **Roles:** `"user"` messages are yours, `"assistant"` messages are the bot's; they must alternate.
- **Streaming:** showing the reply piece by piece as Claude writes it, instead of waiting for the whole thing.
- **Personality through the system prompt:** the same code becomes a study buddy, Sherlock Holmes or a grumpy cat.

## Before you start
- Install (with your virtual environment on):
  ```bash
  pip install anthropic
  ```
  Or the whole Part 4 line: `pip install anthropic fastapi "uvicorn[standard]" pydantic`
- **API key:** `ANTHROPIC_API_KEY` must be set in your terminal (see **Get your API key** in the [Part 4 README](../README.md)). Tip: `CLAUDE_MODEL=claude-haiku-5-5` makes chatting cheaper and faster.
- This folder has two files: `chatbot.py` (the project) and `ai.py` (the helper that talks to Claude).

## Run it
1. Open a terminal in the `ai-from-zero` folder.
2. Start the chatbot:
   ```bash
   cd part-4-chatbots/17-chatbot-with-memory
   python chatbot.py
   ```
3. Tell it your name, chat a bit, then ask "what's my name?". Type `bye` to quit (or press `Ctrl + C`).
4. Now give it a personality by typing one after the file name:
   ```bash
   python chatbot.py "You are Sherlock Holmes. Deduce things about me from what I say."
   ```

### What you should see
The replies appear word by word. Claude's wording will differ, but the conversation goes like this:
```
Chatbot ready! Type 'bye' to quit.

you: Hi, I'm Sam and I love football
bot: Hi Sam! Football is a great thing to love. Do you play yourself, or mostly watch? Which team do you support?

you: what's my name?
bot: Your name is Sam! And you love football. Speaking of which, have you got a match coming up this week?

you: bye
Bye! We exchanged 4 messages.
```
The important bit: the second reply knows your name, even though you only said it in the first message.

## How it works
**The memory trick:**
```
turn 1 sends: [you: "Hi, I'm Sam..."]
turn 2 sends: [you: "Hi, I'm Sam...", bot: "Hi Sam!...", you: "what's my name?"]
turn 3 sends: [ ...everything so far..., you: <new message>]
```
Every turn sends the **whole** list. Claude reads it all from the start, every time.

**chatbot.py**
1. **`personality`** is whatever you typed after `chatbot.py`, or a default study-buddy prompt. It's used as the system prompt.
2. **`conversation = []`** is THE MEMORY: a plain Python list of messages.
3. **The `while True` loop** repeats until you quit:
   - `input("you: ")` waits for you to type. `bye`, `quit`, `exit`, `Ctrl + C` or `Ctrl + D` end the loop; an empty line is skipped, because Claude rejects empty messages.
   - Your message is added: `conversation.append({"role": "user", "content": you})`.
   - `ai.stream(conversation, system=personality)` sends the whole list and gives back the reply in small pieces. Each piece is printed straight away (`end=""` keeps it on one line, `flush=True` shows it immediately) and also added to `reply`.
   - The bot's full reply is added too: `conversation.append({"role": "assistant", "content": reply})`.
4. At the end it prints how many messages were exchanged.

**ai.py** (the helper, shared by every project from here on)
- `client()` creates the Anthropic connection once, and stops with a clear ❌ message if `ANTHROPIC_API_KEY` isn't set.
- `MODEL` is `claude-opus-5-5` unless you set `CLAUDE_MODEL`.
- `_safety_net()` adds the automatic retry-on-another-model option for Opus 5.5 and Sonnet 5.5 (see project 16).
- `stream()` uses `client().beta.messages.stream(...)` and `yield`s each piece of text as it arrives. (`yield` makes a function hand out results one at a time, which is what a `for` loop over it receives.)
- `ask()` is the non-streaming version (used in project 18) and `ask_for_data()` fills in a form (project 20).

## If something goes wrong
- **`❌ ANTHROPIC_API_KEY is not set in this terminal`** → set it in this terminal (Part 4 README, Step 4) and run again.
- **`❌ Your API key is wrong or was deleted`** → copy the key again, or create a new one in the console.
- **It doesn't remember things you said** → check you didn't remove or move either `conversation.append(...)` line, and that you're in the same run (quitting clears the list).
- **`ModuleNotFoundError: No module named 'ai'`** → you're not in this project's folder. `cd part-4-chatbots/17-chatbot-with-memory` first; `ai.py` must sit next to `chatbot.py`.
- **Replies get slower or cost more in a long chat** → that's expected: the whole conversation is sent every turn. Quit and start again for a fresh, cheap chat.

## Try this
1. **Break the memory.** Delete the line `conversation.append({"role": "assistant", "content": reply})`. Ask a question, then ask "what did you just say?". Why does it get confused?
   <details><summary>Hint</summary>

   Claude now only ever sees your messages, never its own replies, so it has no idea what it said. The list is the only memory there is. Put the line back afterwards.
   </details>
2. **Watch the cost grow.** Add `print(f"(memory size: {len(str(conversation))} characters)")` right after the second `conversation.append(...)` line. Chat for 5 turns.
   <details><summary>Hint</summary>

   The number only goes up. Each turn you pay for the *whole* history as input tokens. Real apps trim or summarise old messages when chats get long, and every model has a maximum it can read at once (its **context window**).
   </details>
3. **Remember between runs.** Make the chatbot save `conversation` to a file called `memory.json` when you quit, and load it when it starts, so it remembers you tomorrow.
   <details><summary>Solution</summary>

   Add `import json` and `import os` at the top. Under `conversation = []` add:
   ```python
   if os.path.exists("memory.json"):              # load the memory from last time, if there is one
       with open("memory.json") as f:
           conversation = json.load(f)
   ```
   And just before the final `print(f"Bye! ...")` add:
   ```python
   with open("memory.json", "w") as f:            # save the memory for next time
       json.dump(conversation, f, indent=2)
   ```
   Tell it your name, type `bye`, run it again and ask "who am I?". Delete `memory.json` to make it forget. (Project 18 does the same thing with a proper database.)
   </details>

## Check yourself
1. Where does the chatbot's memory actually live?
2. Why does a long conversation cost more per message than a short one?
3. What does streaming change for the user, and does it change the answer?
4. What would happen if two people shared one `conversation` list?

<details><summary>Answers</summary>

1. In the `conversation` list in your program. Claude itself keeps nothing between requests.
2. Every turn sends the whole history, and you pay for every input token, so each new message carries all the old ones with it.
3. The reply appears as it's written, so the bot feels faster. The answer itself is the same.
4. Claude would see both people's messages as one conversation and mix them up. Each user needs their own list, which is what project 18 does with chat numbers.
</details>

## Learn more (optional)
- Streaming replies (official docs): https://platform.claude.com/docs/en/build-with-claude/streaming
- Context windows, the limit on how much Claude can read at once: https://platform.claude.com/docs/en/build-with-claude/context-windows

## Next
→ [18 · Chatbot API that saves chats](../18-chatbot-api-that-saves-chats)
