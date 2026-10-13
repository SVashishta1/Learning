# 1.3 · Joke & quote API: random picks

**What you build:** `/jokes/random` returns a random joke from a Python list. You can also filter by category, fetch by id, and **add new jokes with POST**.
**Like you're 10:** a joke jar. Pull one out at random, or put a new one in.

## Run it
```bash
cd level-1-apis/03-joke-and-quote-api-random-picks
pip install -r requirements.txt
uvicorn main:app --reload
```
- http://127.0.0.1:8000/jokes/random
- http://127.0.0.1:8000/jokes/random?category=ai
- http://127.0.0.1:8000/jokes/2
- **Add a joke:** open http://127.0.0.1:8000/docs → `POST /jokes` → Try it out → send `{"text": "your joke", "category": "ai"}`

Test: `pytest -v`

## Key ideas
- **Path parameter** `/jokes/{joke_id}` picks ONE thing. **Query parameter** `?category=ai` filters MANY things.
- **POST** sends data in the request **body** as JSON. **Pydantic models** (`class NewJoke(BaseModel)`) describe and validate that JSON. This is the same tool you'll use later to validate LLM outputs!
- **Route order matters:** `/jokes/random` must be defined *before* `/jokes/{joke_id}`, or FastAPI would try to turn "random" into an int.
- New jokes vanish when you restart the server, because they live in memory. Project 1.5 fixes that with a database.

## Your turn
1. Add `DELETE /jokes/{joke_id}`.
2. Add `/jokes/count` returning how many jokes per category (hint: a dict).
3. Add a `rating: int = Field(ge=1, le=5)` to jokes and a `/jokes/top` route.

## Watch
- Request body & Pydantic: https://fastapi.tiangolo.com/tutorial/body/
