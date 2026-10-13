# The brain of the final project: a TEAM of AI agents.
#   Receptionist → picks the right specialist:
#     📚 Librarian   searches YOUR documents (vector database, Part 5)
#     🌍 Researcher  searches the web
#     ✅ Organizer   manages your to-do list (database, Part 1)
#     💬 Chatter     everything else
import sqlite3
from pathlib import Path
from typing import Literal

import chromadb
from pydantic import BaseModel
from pypdf import PdfReader

import ai
from agent import run_agent, tool

# ---------- 📚 the Librarian's vector database ----------
library = chromadb.PersistentClient(path="chroma_data").get_or_create_collection("docs", configuration={"hnsw": {"space": "cosine"}})


def add_document(path: Path) -> int:
    text = "\n".join(p.extract_text() or "" for p in PdfReader(path).pages) if path.suffix == ".pdf" else path.read_text()
    chunks = [c.strip() for c in text.split("\n\n") if c.strip()]
    library.upsert(ids=[f"{path.name}-{i}" for i in range(len(chunks))], documents=chunks,
                   metadatas=[{"source": path.name}] * len(chunks))
    return len(chunks)


def search_my_documents(question):
    found = library.query(query_texts=[question], n_results=min(4, library.count()))
    return "\n\n".join(f"[{m['source']}] {d}" for d, m in zip(found["documents"][0], found["metadatas"][0]))


# ---------- ✅ the Organizer's to-do database ----------
db = sqlite3.connect("tasks.db", check_same_thread=False)
db.execute("CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY, title TEXT, done INTEGER DEFAULT 0)")


def add_task(title):
    db.execute("INSERT INTO tasks (title) VALUES (?)", (title,)); db.commit()
    return f"Added: {title}"


def list_tasks():
    rows = db.execute("SELECT id, title, done FROM tasks").fetchall()
    return "\n".join(f"#{i} {'✅' if d else '⬜'} {t}" for i, t, d in rows) or "No tasks yet."


def finish_task(task_id):
    db.execute("UPDATE tasks SET done = 1 WHERE id = ?", (int(task_id),)); db.commit()
    return f"Task #{task_id} marked done"


# ---------- the team ----------
class Route(BaseModel):
    specialist: Literal["librarian", "researcher", "organizer", "chatter"]


TEAM = {
    "librarian": ("You answer questions using the user's own documents. Always search them first and mention which file the answer came from. "
                  "If they don't contain the answer, say so.",
                  [tool(search_my_documents, "Search the user's documents by meaning", {"question": ("string", "what to look for")})], False),
    "researcher": ("You answer questions about the outside world using web search. Give short answers with source links.", [], True),
    "organizer": ("You manage the user's to-do list. Look at the list before changing it. Confirm what you did.",
                  [tool(add_task, "Add a task", {"title": ("string", "the task")}),
                   tool(list_tasks, "Show all tasks", {}),
                   tool(finish_task, "Mark a task as done", {"task_id": ("integer", "task number")})], False),
    "chatter": ("You are a friendly, encouraging assistant for someone learning AI.", [], False),
}


def handle(message, history):
    route = ai.ask_for_data(
        f"Recent chat: {history[-4:]}\nNew message: {message}", Route,
        system=("Route the message: 'librarian' = about the user's own documents/notes/policies/plans; 'researcher' = news or "
                "facts about the world; 'organizer' = to-do list or tasks; 'chatter' = anything else."))
    instructions, tools, web = TEAM[route.specialist]
    context = "\n".join(f"{m['role']}: {m['content']}" for m in history[-6:])
    used = []
    reply = run_agent(f"Conversation so far:\n{context}\n\nUser: {message}", tools, system=instructions,
                      web_search=web, name=route.specialist, show=False, trace=used)
    return route.specialist, reply, used


for path in sorted(Path("docs").iterdir()):          # load the docs folder when the app starts
    if path.suffix in {".md", ".txt", ".pdf"}:
        add_document(path)
