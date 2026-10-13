# 19 · Chatbot with a web page

**What it does:** your own mini ChatGPT: a chat page in your browser, replies that appear word by word, conversations saved in a database, and a "New chat" button.

## Run it
```bash
cd part-4-chatbots/19-chatbot-with-a-web-page
uvicorn app:app --reload
```
Open http://127.0.0.1:8000 and chat. Refresh the page: your conversation is still there.

## The idea in one sentence
The web page (`page.html`) sends your message to the API (`app.py`), the API sends the saved conversation to Claude, and the reply is **streamed** back piece by piece so you see it being typed.

## Try this
1. Change `PERSONALITY` in `app.py`. Make it a cooking assistant or a language tutor.
2. Change the colours in `page.html` (look for `#2563eb`, the blue of your messages).
3. Run it with `--host 0.0.0.0` and open it on your phone (same Wi-Fi) at `http://<your-computer's-IP>:8000`.
