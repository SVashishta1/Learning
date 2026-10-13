"""Upload a document, get JSON back.  uvicorn api:app --reload"""
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, UploadFile

import llm
from extractor import extract

app = FastAPI(title="Invoice extractor")
client = llm.get_client()


@app.post("/extract")
async def extract_endpoint(file: UploadFile = File(...)):
    suffix = Path(file.filename or "doc.txt").suffix or ".txt"
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(await file.read())
    invoice, problems = extract(client, Path(tmp.name))
    return {"invoice": invoice.model_dump(), "needs_review": bool(problems), "problems": problems}
