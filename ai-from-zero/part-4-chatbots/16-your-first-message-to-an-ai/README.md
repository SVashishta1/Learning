# 16 · Your first message to an AI

**What it does:** sends one question to Claude and prints the answer, plus how many "tokens" (pieces of words) it used. Tokens are what you pay for.

## Run it
Make sure your API key is set (see the Part 4 README), then:
```bash
cd part-4-chatbots/16-your-first-message-to-an-ai
python first_message.py
python first_message.py "Give me 3 fun facts about octopuses"
```

## The idea in one sentence
Talking to an AI is just an API call (like the weather in project 04): you send a **system** message (its role) and a list of **messages**, and you get its reply back.

## Try this
1. Change `system=` to `"You are a pirate. Answer everything like a pirate."`.
2. Set `max_tokens=20` and ask a big question. The answer gets cut off!
3. Ask it to "reply only in JSON with keys name and age about a made-up person".
