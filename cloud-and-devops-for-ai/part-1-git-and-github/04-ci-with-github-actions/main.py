"""Mood API: a tiny "AI" web service that guesses the mood of a sentence.

The "model" here is two word lists, so it runs anywhere for free and its
answers never change. That makes it perfect for learning CI: the tests can
check exact answers. Later lessons swap the word lists for a real language model.
"""

from fastapi import FastAPI
from pydantic import BaseModel, Field

app = FastAPI(title="Mood API")

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
    return {"status": "ok"}


@app.post("/predict")
def predict(body: TextIn):
    # ** unpacks the dictionary, so its keys are added to this one.
    return {"text": body.text, **predict_mood(body.text)}
