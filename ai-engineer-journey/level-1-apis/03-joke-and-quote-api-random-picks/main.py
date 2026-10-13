"""Project 1.3: a joke & quote API.

New ideas: path parameters (/jokes/3), filtering (?category=), and POST bodies validated by Pydantic.
"""
import random

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field

app = FastAPI(title="Joke & Quote API")

JOKES = [
    {"id": 1, "category": "programming", "text": "Why do programmers prefer dark mode? Because light attracts bugs."},
    {"id": 2, "category": "programming", "text": "There are 10 kinds of people: those who understand binary and those who don't."},
    {"id": 3, "category": "ai", "text": "My neural network told a joke. It was over-fitted to my sense of humor."},
    {"id": 4, "category": "ai", "text": "I asked the AI for a gradient joke. It said it was still descending."},
    {"id": 5, "category": "general", "text": "I'm reading a book on anti-gravity. It's impossible to put down."},
]
QUOTES = [
    "The best way to predict the future is to invent it. (Alan Kay)",
    "First, solve the problem. Then, write the code. (John Johnson)",
    "Simple things should be simple, complex things should be possible. (Alan Kay)",
]


class NewJoke(BaseModel):
    # Pydantic checks the incoming JSON: text must be 5-300 chars, category defaults to "general"
    text: str = Field(min_length=5, max_length=300)
    category: str = "general"


@app.get("/jokes")
def list_jokes(category: str | None = None):
    if category:
        return [j for j in JOKES if j["category"] == category]
    return JOKES


@app.get("/jokes/random")
def random_joke(category: str | None = None):
    pool = [j for j in JOKES if category in (None, j["category"])]
    if not pool:
        raise HTTPException(404, f"No jokes in category '{category}'")
    return random.choice(pool)


@app.get("/jokes/{joke_id}")
def get_joke(joke_id: int):
    for joke in JOKES:
        if joke["id"] == joke_id:
            return joke
    raise HTTPException(status_code=404, detail="Joke not found")


@app.post("/jokes", status_code=201)
def add_joke(joke: NewJoke):
    new = {"id": max(j["id"] for j in JOKES) + 1, **joke.model_dump()}
    JOKES.append(new)
    return new


@app.get("/quotes/random")
def random_quote():
    return {"quote": random.choice(QUOTES)}
