# 1.3 · Joke & quote API: random picks + POST

**What you'll build:** a joke API: `/jokes/random` picks a random joke, `?category=ai` filters, `/jokes/2` fetches one by id, and `POST /jokes` adds your own joke (checked by Pydantic). Plus a random quote route.
**Like you're 10:** a joke jar. Pull one out at random, look for a specific one, or put a new one in. The jar refuses scraps of paper too small to hold a joke.
**Time:** ~1 h · **Builds on:** [1.2 · Calculator API](../02-calculator-api-query-parameters) · **Needs:** nothing extra

## Why this matters
So far your API only *gave* answers. Real APIs also *receive* data: a chat message, a document to summarise, a new user. That data arrives as JSON in a **POST** request, and it must be validated before you trust it. Pydantic, the validator you meet here, is the same tool you'll use in Level 7 to check that an LLM's output has the right shape.

## What you'll learn
- **Path parameter vs query parameter:** `/jokes/{joke_id}` picks ONE thing; `?category=ai` filters MANY things.
- **POST and request bodies:** POST sends data as JSON in the request **body**, not in the URL.
- **Pydantic models:** a class like `NewJoke(BaseModel)` describes the JSON you accept and rejects anything else with a 422.
- **404 Not Found:** the right answer when someone asks for a thing that doesn't exist.
- **Route order:** FastAPI checks routes top to bottom, so `/jokes/random` must come before `/jokes/{joke_id}`.

## Before you start
```bash
cd level-1-apis/03-joke-and-quote-api-random-picks
pip install -r requirements.txt
```
- `fastapi`, `uvicorn[standard]`: web framework and server. FastAPI installs **Pydantic** for you.
- `pytest`, `httpx`, `httpx2`: to run the tests.

No API key needed.

## Run it
1. Start the server: `uvicorn main:app --reload`
2. Open in your browser:
   - http://127.0.0.1:8000/jokes/random (refresh a few times)
   - http://127.0.0.1:8000/jokes/random?category=ai
   - http://127.0.0.1:8000/jokes/2
   - http://127.0.0.1:8000/jokes/999
   - http://127.0.0.1:8000/quotes/random
3. Add a joke: open http://127.0.0.1:8000/docs → `POST /jokes` → **Try it out** → body `{"text": "your joke", "category": "ai"}` → **Execute**. Or, in a second terminal:
   ```bash
   curl -X POST http://127.0.0.1:8000/jokes -H "Content-Type: application/json" -d '{"text": "Why did the AI cross the road? It was in the training data.", "category": "ai"}'
   ```
   (Windows PowerShell: use `curl.exe` instead of `curl`.)
4. Run the tests: `pytest -v`

### What you should see
```
GET  /jokes/random              {"id":2,"category":"programming","text":"There are 10 kinds of people: those who understand binary and those who don't."}
GET  /jokes/random?category=ai  {"id":3,"category":"ai","text":"My neural network told a joke. It was over-fitted to my sense of humor."}
GET  /jokes/999                 {"detail":"Joke not found"}                          (status 404)
GET  /jokes/random?category=cooking   {"detail":"No jokes in category 'cooking'"}    (status 404)
GET  /quotes/random             {"quote":"Simple things should be simple, complex things should be possible. (Alan Kay)"}
POST /jokes                     {"id":6,"text":"Why did the AI cross the road? It was in the training data.","category":"ai"}   (status 201)
POST /jokes {"text": "hi"}      {"detail":[{"type":"string_too_short","loc":["body","text"],"msg":"String should have at least 5 characters",...}]}   (status 422)
```
Your random picks will differ. Look at the new joke's `"id":6`: the server picked the next free id. The 422 points at `["body","text"]`: the problem is in the JSON body, field `text`.

## How it works
1. **The data:** `JOKES` is a list of dicts and `QUOTES` a list of strings, both kept in memory (in the running Python program).
2. **`list_jokes(category)`**: `category: str | None = None` means "optional, default None". With a category, a list comprehension keeps only matching jokes.
3. **`random_joke(category)`** builds a `pool` of candidates (`category in (None, j["category"])` is true when there's no filter, or when it matches), returns 404 if the pool is empty, else `random.choice(pool)`.
4. **`get_joke(joke_id: int)`** loops through `JOKES` and returns the match, or raises a 404. Because it's defined *after* `/jokes/random`, the word "random" never reaches it (it would fail to become an `int`).
5. **`NewJoke(BaseModel)`** says: `text` must be a string of 5 to 300 characters; `category` is optional and defaults to `"general"`. FastAPI reads the request body, builds a `NewJoke`, and returns 422 automatically if that fails.
6. **`add_joke(joke)`** picks the next id with `max(..., default=0) + 1` (the `default=0` keeps it working even if the list is ever empty), merges it with `joke.model_dump()` (the Pydantic object as a dict), appends it, and returns it with status **201 Created**.

New jokes vanish when you restart the server, because they live only in memory. Project 1.5 fixes that with a database.

## If something goes wrong
- **`GET /jokes/random` returns 422 "unable to parse string as an integer"** → you moved `/jokes/{joke_id}` above `/jokes/random`. Put the fixed route first.
- **POST returns 422 with `"type":"json_invalid"`** → the body isn't valid JSON. Use double quotes: `{"text": "..."}`, not `{'text': '...'}`.
- **curl in PowerShell complains about `-H` or `-d`** → PowerShell's `curl` is a different program. Type `curl.exe`, or use the `/docs` page instead.
- **Your added joke disappeared** → the server restarted (`--reload` restarts on every save). Memory is wiped on restart; that's expected here.
- **`405 Method Not Allowed`** → you sent GET to a POST-only route (opening `/jokes` in the browser is fine, but adding needs POST).

## Try this
1. Add `DELETE /jokes/{joke_id}` that removes a joke (404 if it doesn't exist).
   <details><summary>Solution</summary>

   ```python
   @app.delete("/jokes/{joke_id}", status_code=204)
   def delete_joke(joke_id: int):
       JOKES.remove(get_joke(joke_id))   # get_joke already raises 404 for unknown ids
   ```
   204 means "done, nothing to send back". Test it in `/docs`.
   </details>
2. Add `/jokes/count` returning how many jokes each category has, like `{"programming": 2, "ai": 2, "general": 1}`.
   <details><summary>Solution</summary>

   ```python
   @app.get("/jokes/count")
   def count_jokes():
       counts = {}
       for j in JOKES:
           counts[j["category"]] = counts.get(j["category"], 0) + 1
       return counts
   ```
   Put it **above** `/jokes/{joke_id}`, for the same reason as `/jokes/random`.
   </details>
3. Add `rating: int = Field(default=3, ge=1, le=5)` to `NewJoke`, and a `/jokes/top` route that returns the highest-rated joke.
   <details><summary>Solution</summary>

   `ge` = greater than or equal, `le` = less than or equal, so a rating of 6 is a 422. The old jokes have no rating, so use `.get` with a default:
   ```python
   @app.get("/jokes/top")
   def top_joke():
       return max(JOKES, key=lambda j: j.get("rating", 3))
   ```
   Again, define it above `/jokes/{joke_id}`.
   </details>

## Check yourself
1. When would you use `/jokes/{joke_id}` and when `/jokes?category=ai`?
2. Where is the data of a POST request, and how does FastAPI know its shape?
3. Why does the order of `/jokes/random` and `/jokes/{joke_id}` matter?
4. Why return 201 instead of 200 from `POST /jokes`?

<details><summary>Answers</summary>

1. Path parameters identify one specific thing (joke number 2). Query parameters filter or tweak a list (only AI jokes).
2. In the request body, as JSON. The Pydantic model in the function signature (`joke: NewJoke`) tells FastAPI what to expect and how to validate it.
3. FastAPI uses the first route that matches. If `/jokes/{joke_id}` came first, "random" would be treated as a joke id, fail to become an `int`, and return 422.
4. 201 means "Created": it tells the caller something new now exists, which is more precise than a plain "OK".
</details>

## Learn more (optional)
- Request body & Pydantic: https://fastapi.tiangolo.com/tutorial/body/
- Path parameters: https://fastapi.tiangolo.com/tutorial/path-params/
- HTTP methods (GET, POST, ...) explained: https://www.youtube.com/results?search_query=http+methods+get+post+put+delete+explained

## Next
→ [1.4 · To-do API: CRUD in memory](../04-todo-api-crud-in-memory)
