"""Optional: the two models behind an API.  uvicorn api:app --reload"""
from fastapi import FastAPI
from pydantic import BaseModel, Field

from translate_and_summarize import summarize, translate   # loads both models once, when the server starts

app = FastAPI(title="Translate & summarise")


class Text(BaseModel):
    text: str = Field(min_length=1, max_length=5000)


@app.post("/translate")
def translate_endpoint(t: Text):
    return {"french": translate(t.text)}


@app.post("/summarize")
def summarize_endpoint(t: Text):
    return {"summary": summarize(t.text, max_length=80, min_length=15)}
