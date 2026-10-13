# A web app: upload documents and CHAT with them. RAG (project 24) + chat memory (Part 4) + a web page.
import shutil
from pathlib import Path

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

import rag

app = FastAPI()
rag.add_folder("docs")
chats: dict[str, list] = {}          # chat memory per browser tab (kept in memory for simplicity)


class Question(BaseModel):
    chat_id: str
    text: str


@app.post("/ask")
def ask(q: Question):
    history = chats.setdefault(q.chat_id, [])
    reply, sources = rag.answer(q.text, conversation=history[-6:])    # remember the last 3 exchanges
    history += [{"role": "user", "content": q.text}, {"role": "assistant", "content": reply}]
    return {"reply": reply, "sources": [{"n": n, "source": s["source"], "preview": s["text"][:160]} for n, s in enumerate(sources, 1)]}


@app.post("/upload")
def upload(file: UploadFile = File(...)):
    path = Path("docs") / Path(file.filename).name
    with path.open("wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"file": path.name, "chunks": rag.add_document(path)}


@app.get("/documents")
def documents():
    return sorted({m["source"] for m in rag.library.get()["metadatas"]})


@app.get("/")
def page():
    return FileResponse("page.html")
