"""Mood API: a tiny "AI" web service that guesses the mood of a sentence.

Same app as lesson 04, plus one new idea: it reads its version number from an
environment variable, so you can change it with `docker run -e` without
touching the code.
"""

import os

from fastapi import FastAPI
from pydantic import BaseModel, Field

# os.getenv("NAME", "default") reads an environment variable, or uses the default.
APP_VERSION = os.getenv("APP_VERSION", "dev")

app = FastAPI(title="Mood API", version=APP_VERSION)

POSITIVE_WORDS = {
    "good",
    "great",
    "love",
    "happy",
    "excellent",
    "amazing",
    "awesome",
    "nice",
    "helpful",
}
NEGATIVE_WORDS = {
    "bad",
    "terrible",
    "hate",
    "sad",
    "awful",
    "horrible",
    "angry",
    "broken",
    "useless",
}


class TextIn(BaseModel):
    # Field(...) adds rules: at least 1 character, at most 1,000.
    text: str = Field(min_length=1, max_length=1000)


def predict_mood(text: str) -> dict:
    """Return {"label": ..., "score": ...} for one piece of text."""
    # Lower-case every word and strip punctuation, so "Great!" counts as "great".
    words = [word.strip(".,!?;:\"'()").lower() for word in text.split()]
    score = sum(word in POSITIVE_WORDS for word in words) - sum(
        word in NEGATIVE_WORDS for word in words
    )
    if score > 0:
        label = "positive"
    elif score < 0:
        label = "negative"
    else:
        label = "neutral"
    return {"label": label, "score": score}


@app.get("/health")
def health():
    # Servers, load balancers and Docker call this to ask "are you alive?".
    return {"status": "ok", "version": APP_VERSION}


@app.post("/predict")
def predict(body: TextIn):
    # ** unpacks the dictionary, so its keys are added to this one.
    return {"text": body.text, **predict_mood(body.text)}
