# Your own mini ChatGPT: a web page + an API that streams replies word by word and saves chats.
import sqlite3

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, StreamingResponse
from pydantic import BaseModel

import ai

ai.client()          # stop straight away, with a clear message, if your API key isn't set
app = FastAPI()
db = sqlite3.connect("chats.db", check_same_thread=False)                 # the file is created on first run
db.execute("CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY, chat_id TEXT, role TEXT, content TEXT)")
PERSONALITY = "You are a helpful, cheerful assistant. Use short paragraphs."


class Message(BaseModel):
    chat_id: str
    text: str


def load_chat(chat_id):
    rows = db.execute("SELECT role, content FROM messages WHERE chat_id = ? ORDER BY id", (chat_id,)).fetchall()
    return [{"role": r, "content": c} for r, c in rows]


@app.post("/chat")
def chat(message: Message):
    if not message.text.strip():
        raise HTTPException(400, "The message is empty")
    db.execute("INSERT INTO messages (chat_id, role, content) VALUES (?, 'user', ?)", (message.chat_id, message.text))
    db.commit()
    history = load_chat(message.chat_id)

    def live_reply():
        reply = ""
        for piece in ai.stream(history, system=PERSONALITY):
            reply += piece
            yield piece                       # send each piece to the browser immediately
        db.execute("INSERT INTO messages (chat_id, role, content) VALUES (?, 'assistant', ?)", (message.chat_id, reply))
        db.commit()

    return StreamingResponse(live_reply(), media_type="text/plain")


@app.get("/history/{chat_id}")
def history(chat_id: str):
    return load_chat(chat_id)


@app.get("/")
def page():
    return FileResponse("page.html")
