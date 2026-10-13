# 18 · Chatbot API that saves chats

**What it does:** puts your chatbot behind an API (Part 1 skills!). Each conversation gets a number, and every message is saved in a database, so chats survive restarts.

## Run it
```bash
cd part-4-chatbots/18-chatbot-api-that-saves-chats
uvicorn main:app --reload
```
At http://127.0.0.1:8000/docs:
1. **POST /chats** → you get `{"chat_id": 1}`
2. **POST /chats/1** with `{"text": "Hi, I'm Sam and I love football"}`
3. **POST /chats/1** with `{"text": "What do I love?"}` → it remembers
4. **GET /chats/1** → the whole saved conversation

Restart the server and continue chat 1. It still remembers.

## The idea in one sentence
Same memory trick as project 17, but the conversation is stored in a database table instead of a Python list, so many users can each have their own saved chats.

## Try this
1. Start chat 2 and check that it doesn't know about chat 1.
2. Change `PERSONALITY` to make it a customer-support agent for a pizza shop.
