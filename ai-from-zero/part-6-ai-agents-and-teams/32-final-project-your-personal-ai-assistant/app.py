# The web app for your personal AI assistant.  Run: uvicorn app:app --reload   then open http://127.0.0.1:8000
import shutil
from pathlib import Path

from fastapi import FastAPI, File, UploadFile
from fastapi.responses import FileResponse
from pydantic import BaseModel

import assistant

app = FastAPI()
history = []                      # the conversation (one user, kept in memory)


class Message(BaseModel):
    text: str


@app.post("/chat")
def chat(message: Message):
    specialist, reply, tools_used = assistant.handle(message.text, history)
    history.extend([{"role": "user", "content": message.text}, {"role": "assistant", "content": reply}])
    return {"specialist": specialist, "reply": reply, "tools_used": tools_used}


@app.post("/upload")
def upload(file: UploadFile = File(...)):
    path = Path("docs") / Path(file.filename).name
    with path.open("wb") as f:
        shutil.copyfileobj(file.file, f)
    return {"file": path.name, "chunks": assistant.add_document(path)}


@app.get("/tasks")
def tasks():
    return {"tasks": assistant.list_tasks()}


@app.get("/")
def page():
    return FileResponse("page.html")
