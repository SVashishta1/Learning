# 16 · Your first message to an AI

**What you'll build:** a short program that sends one question to Claude and prints the answer, plus how many **tokens** (pieces of words) it used. Tokens are what you pay for.
**Time:** ~45 min · **Builds on:** [04 · Your code calls another API](../../part-1-apis/04-your-code-calls-another-api) · **Needs:** an Anthropic API key (see the [Part 4 README](../README.md))

## Why this matters
Almost every AI feature you see in apps (chat assistants, "summarise this", smart search) is ordinary code sending a request like this one to a model's API. Knowing the four parts of a request (model, system, messages, max_tokens) and reading the reply and token counts is the first skill of an AI engineer.

## What you'll learn
- **Model:** which Claude you're talking to (for example `claude-opus-5-5` or the cheaper `claude-haiku-5-5`).
- **System prompt:** the AI's role and rules ("You are a friendly teacher").
- **Messages:** the conversation so far, as a list of `{"role": ..., "content": ...}` items.
- **Tokens and `max_tokens`:** you pay per token in and out; `max_tokens` caps how long the reply can be.
- **Content blocks and stop reason:** the reply comes in pieces ("blocks"), plus a note saying why it stopped.

## Before you start
- Install (with your virtual environment on):
  ```bash
  pip install anthropic
  ```
  `anthropic` is Anthropic's official Python library. Or install everything for Part 4 at once: `pip install anthropic fastapi "uvicorn[standard]" pydantic`
- **You need an API key.** Follow **Get your API key** in the [Part 4 README](../README.md) (account, about $5 of credit, create the key, set `ANTHROPIC_API_KEY` in your terminal).
- Optional: set `CLAUDE_MODEL=claude-haiku-5-5` for the cheapest model (Step 5 in the Part 4 README).

## Run it
1. Open a terminal in the `ai-from-zero` folder and make sure your key is set in **this** terminal.
2. Run it with the built-in question:
   ```bash
   cd part-4-chatbots/16-your-first-message-to-an-ai
   python first_message.py
   ```
3. Now ask your own question by typing it after the file name:
   ```bash
   python first_message.py "Give me 3 fun facts about octopuses"
   ```

### What you should see
Claude's wording is different every time, but it looks like this:
```
An API is like a waiter in a restaurant. You tell the waiter what you want, and they go to the kitchen and bring it back. Apps use APIs to ask other programs for things, like today's weather or a map!

(used 33 tokens in, 118 tokens out; stopped because: end_turn)
```
Look at the last line:
- **tokens in** = your system prompt + question. **tokens out** = the reply, plus some hidden "thinking" Claude did before answering (Claude 5 models think first; you pay for it as output).
- **stopped because: end_turn** means Claude finished naturally. `max_tokens` would mean it hit your length limit.

## How it works
```
first_message.py ──HTTPS request──→ Anthropic API ──→ Claude
 (model, system,                                        │
  messages, key)  ←──── JSON reply (content blocks, ────┘
                         usage, stop_reason)
```
1. **Key check.** If `ANTHROPIC_API_KEY` isn't set, the program stops with a ❌ message telling you where to fix it.
2. **`client = anthropic.Anthropic()`** creates the connection. It finds your key in the `ANTHROPIC_API_KEY` setting by itself.
3. **`model = os.getenv("CLAUDE_MODEL", "claude-opus-5-5")`** uses your `CLAUDE_MODEL` setting if you made one, otherwise Opus 5.5.
4. **`question`** is whatever you typed after the file name (`sys.argv[1:]`), or a default question.
5. **`safety_net`**: on Opus 5.5 and Sonnet 5.5 it adds two options. In the rare case Claude declines a request, Anthropic's servers automatically retry on another model. `betas=[...]` switches on this newer feature; that's why the code calls `client.beta.messages.create` instead of `client.messages.create`.
6. **`client.beta.messages.create(...)`** sends the request, exactly like calling the weather API in project 04, just with these fields:
   - `max_tokens=1000`: the longest reply allowed (thinking counts too).
   - `system="You are a friendly teacher."`: the role.
   - `messages=[{"role": "user", "content": question}]`: the conversation, here just one user message. `"user"` is you; Claude's replies have the role `"assistant"`.
7. **Reading the reply.** `response.content` is a list of **blocks**. There may be a `thinking` block (kept hidden) and a `text` block (the answer). The code joins the text blocks and prints them. `response.usage` has the token counts and `response.stop_reason` says why it stopped.

The model itself remembers nothing between runs. Each request has to include everything Claude should know. That's the key to the next project.

## If something goes wrong
- **`❌ ANTHROPIC_API_KEY is not set in this terminal`** → set it (Part 4 README, Step 4) in the same terminal window, then run again.
- **`anthropic.AuthenticationError: Error code: 401`** → the key is wrong. Copy it again (it starts with `sk-ant-`, no spaces), or make a new one in the console.
- **`Your credit balance is too low to access the Anthropic API`** → add credit in the console under Billing.
- **`anthropic.NotFoundError: Error code: 404 ... model`** → `CLAUDE_MODEL` has a typo. Use `claude-haiku-5-5`, `claude-sonnet-5-5` or `claude-opus-5-5`.
- **`ModuleNotFoundError: No module named 'anthropic'`** → turn on your virtual environment and run `pip install anthropic`.

## Try this
1. **Give it a personality.** Change `system=` to `"You are a pirate. Answer everything like a pirate."` and run it again.
   <details><summary>Hint</summary>

   The question is the same, but the answer is full of "Arr!". The system prompt is how apps give an AI its job, tone and rules, for example "You are a support agent for Pizza Palace. Only talk about pizza orders."
   </details>
2. **Hit the limit.** Set `max_tokens=20` and ask a big question, like `python first_message.py "Explain how the internet works"`.
   <details><summary>Hint</summary>

   The answer is cut off mid-sentence, or may even be empty, and the last line says `stopped because: max_tokens`. Empty happens because the hidden thinking also counts towards the limit and used it all up. In real apps, always check the stop reason before trusting a reply.
   </details>
3. **Write a conversation by hand.** Change `messages=` so it contains three messages: you say your favourite colour, Claude says "Got it!", then you ask what your favourite colour is.
   <details><summary>Solution</summary>

   ```python
       messages=[
           {"role": "user", "content": "My favourite colour is green. Remember it."},
           {"role": "assistant", "content": "Got it! Your favourite colour is green."},
           {"role": "user", "content": "What's my favourite colour?"},
       ],
   ```
   Claude answers "green" because the whole conversation is in the request. Notice that "tokens in" went up: you pay for the history too. Project 17 builds this list automatically.
   </details>

## Check yourself
1. What's the difference between the `system` prompt and the `messages`?
2. Why might "tokens out" be bigger than the number of words in the reply?
3. What does `stop_reason` tell you, and which value means the reply was cut short?
4. If you run the program twice, does Claude remember the first question? Why or why not?

<details><summary>Answers</summary>

1. `system` sets the AI's role and rules for the whole conversation. `messages` is the conversation itself: what the user said and what the assistant replied.
2. A token is only part of a word (about ¾ of a word on average), and the count also includes Claude's hidden thinking.
3. Why Claude stopped writing. `end_turn` means it finished; `max_tokens` means it hit your limit and the reply is cut short.
4. No. Each request is independent; the model has no memory between requests. To "remember", you must send the earlier messages again.
</details>

## Learn more (optional)
- Anthropic's list of Claude models (names, prices, what each is good at): https://platform.claude.com/docs/en/about-claude/models/overview
- What each API error means: https://platform.claude.com/docs/en/api/errors
- Search: "what are LLM tokens" https://www.youtube.com/results?search_query=what+are+tokens+large+language+models

## Next
→ [17 · Chatbot with memory](../17-chatbot-with-memory)
