"""Upload a document, get JSON back.  uvicorn api:app --reload"""
import os
import tempfile
from pathlib import Path

from fastapi import FastAPI, File, UploadFile

import llm
from extractor import extract

app = FastAPI(title="Invoice extractor")
client = None    # created on the first request, so the app (and its tests) can start without a key


@app.post("/extract")
def extract_endpoint(file: UploadFile = File(...)):
    global client
    client = client or llm.get_client()
    suffix = Path(file.filename or "doc.txt").suffix or ".txt"     # keep ".pdf" so extract() knows it's a PDF
    with tempfile.NamedTemporaryFile(suffix=suffix, delete=False) as tmp:
        tmp.write(file.file.read())
    try:
        invoice, problems = extract(client, Path(tmp.name))
    finally:
        os.remove(tmp.name)                                       # don't leave customer documents lying around
    return {"invoice": invoice.model_dump(), "needs_review": bool(problems), "problems": problems}
