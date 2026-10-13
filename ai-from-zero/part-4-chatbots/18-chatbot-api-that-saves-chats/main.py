# A chatbot API: many separate chats, all saved in a database (chats.db).
import sqlite3

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import ai

app = FastAPI()
db = sqlite3.connect("chats.db", check_same_thread=False)
db.execute("CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY, chat_id INTEGER, role TEXT, content TEXT)")
PERSONALITY = "You are a friendly assistant. Keep answers under 120 words."


class Message(BaseModel):
    text: str


def load_chat(chat_id):
    rows = db.execute("SELECT role, content FROM messages WHERE chat_id = ? ORDER BY id", (chat_id,)).fetchall()
    return [{"role": role, "content": content} for role, content in rows]


def save(chat_id, role, content):
    db.execute("INSERT INTO messages (chat_id, role, content) VALUES (?, ?, ?)", (chat_id, role, content))
    db.commit()


@app.post("/chats")
def new_chat():
    last = db.execute("SELECT MAX(chat_id) FROM messages").fetchone()[0] or 0
    return {"chat_id": last + 1}


@app.post("/chats/{chat_id}")
def send_message(chat_id: int, message: Message):
    save(chat_id, "user", message.text)
    reply = ai.ask(load_chat(chat_id), system=PERSONALITY)    # send the WHOLE saved chat = memory
    save(chat_id, "assistant", reply)
    return {"reply": reply}


@app.get("/chats/{chat_id}")
def read_chat(chat_id: int):
    chat = load_chat(chat_id)
    if not chat:
        raise HTTPException(404, "No such chat")
    return chat
