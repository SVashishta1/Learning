"""RAG as an API.  uvicorn app:app --reload  ->  POST /ask {"question": "..."}"""
import shutil
from pathlib import Path

from fastapi import FastAPI, File, UploadFile
from pydantic import BaseModel, Field

import llm
from rag import Embedder, Index, answer

app = FastAPI(title="Ask your documents")
state = {"index": Index(Embedder()).build("docs"), "client": None}


class Question(BaseModel):
    question: str = Field(min_length=3, max_length=1000)
    k: int = Field(4, ge=1, le=10)


@app.post("/ask")
def ask(q: Question):
    state["client"] = state["client"] or llm.get_client()
    return answer(state["client"], state["index"], q.question, q.k)


@app.post("/documents")
async def upload(file: UploadFile = File(...)):
    dest = Path("docs") / Path(file.filename).name
    with dest.open("wb") as f:
        shutil.copyfileobj(file.file, f)
    state["index"] = Index(state["index"].embedder).build("docs")          # re-index (fine for small collections)
    return {"indexed_chunks": len(state["index"].chunks), "added": dest.name}


@app.get("/documents")
def list_docs():
    return sorted({c.source.split(" p.")[0] for c in state["index"].chunks})
