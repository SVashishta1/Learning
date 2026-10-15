# A chatbot API: many separate chats, all saved in a database (chats.db).
import sqlite3

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

import ai

ai.client()          # stop straight away, with a clear message, if your API key isn't set
app = FastAPI()
db = sqlite3.connect("chats.db", check_same_thread=False)                 # the file is created on first run
db.execute("CREATE TABLE IF NOT EXISTS chats (id INTEGER PRIMARY KEY)")    # one row per chat: its number
db.execute("CREATE TABLE IF NOT EXISTS messages (id INTEGER PRIMARY KEY, chat_id INTEGER, role TEXT, content TEXT)")
PERSONALITY = "You are a friendly assistant. Keep answers under 120 words."


class Message(BaseModel):
    text: str


def chat_exists(chat_id):
    return db.execute("SELECT 1 FROM chats WHERE id = ?", (chat_id,)).fetchone() is not None


def load_chat(chat_id):
    rows = db.execute("SELECT role, content FROM messages WHERE chat_id = ? ORDER BY id", (chat_id,)).fetchall()
    return [{"role": role, "content": content} for role, content in rows]


def save(chat_id, role, content):
    db.execute("INSERT INTO messages (chat_id, role, content) VALUES (?, ?, ?)", (chat_id, role, content))
    db.commit()


@app.post("/chats")
def new_chat():
    chat_id = db.execute("INSERT INTO chats DEFAULT VALUES").lastrowid   # the database picks the next number
    db.commit()
    return {"chat_id": chat_id}


@app.post("/chats/{chat_id}")
def send_message(chat_id: int, message: Message):
    if not chat_exists(chat_id):
        raise HTTPException(404, "No such chat. Create one first with POST /chats")
    if not message.text.strip():
        raise HTTPException(400, "The message is empty")
    save(chat_id, "user", message.text)
    reply = ai.ask(load_chat(chat_id), system=PERSONALITY)    # send the WHOLE saved chat = memory
    save(chat_id, "assistant", reply)
    return {"reply": reply}


@app.get("/chats/{chat_id}")
def read_chat(chat_id: int):
    if not chat_exists(chat_id):
        raise HTTPException(404, "No such chat")
    return load_chat(chat_id)
