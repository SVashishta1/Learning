"""Optional: the two models behind an API.  uvicorn api:app --reload"""
from fastapi import FastAPI
from pydantic import BaseModel, Field
from transformers import pipeline

app = FastAPI(title="Translate & summarise")
translator = pipeline("translation", model="Helsinki-NLP/opus-mt-en-fr")
summarizer = pipeline("summarization", model="sshleifer/distilbart-cnn-12-6")


class Text(BaseModel):
    text: str = Field(min_length=1, max_length=5000)


@app.post("/translate")
def translate(t: Text):
    return {"french": translator(t.text)[0]["translation_text"]}


@app.post("/summarize")
def summarize(t: Text):
    return {"summary": summarizer(t.text, max_length=80, min_length=15, do_sample=False)[0]["summary_text"]}
