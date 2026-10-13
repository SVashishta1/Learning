# 17 · Chatbot with memory

**What it does:** a chatbot in your terminal that remembers everything you've said, types its answers live, and can have any personality you give it.

## Run it
```bash
cd part-4-chatbots/17-chatbot-with-memory
python chatbot.py
python chatbot.py "You are Sherlock Holmes. Deduce things about me from what I say."
```
Tell it your name, chat a bit, then ask "what's my name?". It remembers!

## The idea in one sentence
The AI itself forgets everything between messages, so **we** keep the whole conversation in a list and send it again every time. That list *is* the memory.

## Try this
1. Delete the line `conversation.append({"role": "assistant", ...})`. Now ask it what it said a moment ago. Why does it get confused?
2. Print `len(str(conversation))` after each turn. The conversation (and the cost) grows with every message.
