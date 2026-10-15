# 1.4 · To-do API: CRUD in memory

**What you'll build:** a to-do API where you can create, read, update and delete tasks. These four actions (**CRUD**) are behind almost every app you use.
**Like you're 10:** a notebook. Write a task (Create), look at it (Read), tick it off (Update), tear out the page (Delete).
**Time:** ~1.5 h · **Builds on:** [1.3 · Joke & quote API](../03-joke-and-quote-api-random-picks) · **Needs:** nothing extra

## Why this matters
Almost every backend is CRUD on some kind of "thing": users, orders, messages, documents. AI apps are no different: a chatbot stores conversations, a RAG app stores documents, an agent stores tasks. Learning the standard CRUD pattern (verbs, routes, status codes, input vs output models) means you can read and build most APIs out there.

## What you'll learn
- **CRUD ↔ HTTP verbs:** Create = POST, Read = GET, Update = PATCH, Delete = DELETE.
- **Input and output models:** what a client sends (`TodoCreate`) is different from what you return (`Todo`, with an id and timestamp).
- **Partial updates:** PATCH changes only the fields the client sends (`exclude_unset=True`).
- **Status codes for CRUD:** 201 Created, 200 OK, 204 No Content, 404 Not Found.
- **`response_model`:** tells FastAPI the exact shape of the reply, and it filters and documents it for you.

## Before you start
```bash
cd level-1-apis/04-todo-api-crud-in-memory
pip install -r requirements.txt
```
- `fastapi`, `uvicorn[standard]`: web framework and server.
- `pytest`, `httpx`, `httpx2`: to run the tests.

No API key needed.

## Run it
1. Start the server: `uvicorn main:app --reload`
2. Use http://127.0.0.1:8000/docs to POST a todo, then GET `/todos`, PATCH it with `{"done": true}`, and DELETE it.
3. Or use curl in a second terminal (on Windows PowerShell, type `curl.exe`):
   ```bash
   curl -X POST localhost:8000/todos -H "Content-Type: application/json" -d '{"title":"buy milk"}'
   curl -X POST localhost:8000/todos -H "Content-Type: application/json" -d '{"title":"learn FastAPI"}'
   curl localhost:8000/todos
   curl -X PATCH localhost:8000/todos/1 -H "Content-Type: application/json" -d '{"done":true}'
   curl "localhost:8000/todos?done=true"
   curl -X DELETE localhost:8000/todos/1 -i
   curl localhost:8000/todos/1
   ```
4. Run the tests: `pytest -v`

### What you should see
The curl commands above print, in order:
```
{"title":"buy milk","done":false,"id":1,"created_at":"2026-10-15T03:55:04.576291Z"}
{"title":"learn FastAPI","done":false,"id":2,"created_at":"2026-10-15T03:55:04.601075Z"}
[{"title":"buy milk","done":false,"id":1,...},{"title":"learn FastAPI","done":false,"id":2,...}]
{"title":"buy milk","done":true,"id":1,"created_at":"2026-10-15T03:55:04.576291Z"}
[{"title":"buy milk","done":true,"id":1,"created_at":"2026-10-15T03:55:04.576291Z"}]
HTTP/1.1 204 No Content
{"detail":"Todo 1 not found"}
```
After the PATCH, only `done` changed: the title and timestamp were kept. After the DELETE, the todo is gone (404). `-i` makes curl show the status line, because a 204 has no body to print.

## How it works
| CRUD | HTTP verb | Route | Function | Success code |
|------|-----------|-------|----------|--------------|
| Create | POST | `/todos` | `create_todo` | 201 Created |
| Read | GET | `/todos`, `/todos/{id}` | `list_todos`, `get_todo` | 200 OK |
| Update | PATCH | `/todos/{id}` | `update_todo` | 200 OK |
| Delete | DELETE | `/todos/{id}` | `delete_todo` | 204 No Content |

1. **Three Pydantic models for one thing.** `TodoCreate` is what clients send (`title`, optional `done`). `TodoUpdate` has every field optional, because a PATCH may change just one. `Todo(TodoCreate)` *inherits* those fields and adds `id` and `created_at`: that's what you return. Clients never choose their own id.
2. **Storage:** `todos: list[Todo] = []` and `next_id = 1` live in memory.
3. **`find(todo_id)`** loops through `todos` and raises a 404 if nothing matches. Every route that needs one todo reuses it.
4. **`create_todo`** builds a `Todo` with the next id and the current UTC time, appends it, and bumps `next_id`. `global next_id` is needed because the function changes a variable defined outside it.
5. **`list_todos(done)`**: `/todos` returns everything, `/todos?done=true` only finished ones.
6. **`update_todo`**: `changes.model_dump(exclude_unset=True, exclude_none=True)` gives only the fields the client actually sent (and treats `null` as "leave it alone"). `setattr(todo, field, value)` then sets each one, so `{"done": true}` never wipes the title.
7. **`delete_todo`** removes the todo and returns `Response(status_code=204)`: done, nothing to say.

## If something goes wrong
- **`405 Method Not Allowed`** → wrong verb for that route, for example `curl localhost:8000/todos/1 -X PUT` (this API uses PATCH, not PUT).
- **`422` with `"loc":["body"]` and `"Input should be a valid dictionary or object to extract fields from"`** → you forgot `-H "Content-Type: application/json"`, so FastAPI didn't read the body as JSON. (An empty body gives `"Field required"` instead.)
- **`{"detail":"Todo 1 not found"}` right after starting** → the list is empty after every restart, and ids keep counting up (deleted ids are never reused). GET `/todos` to see what exists.
- **Your todos vanished** → `--reload` restarted the server when you saved a file. Memory is wiped. That's the problem 1.5 solves.
- **curl on Windows errors on `-H`/`-d`** → use `curl.exe`, and in PowerShell put the JSON in double quotes with escaped inner quotes, or just use `/docs`.

## Try this
1. Add `GET /todos/stats` returning `{"total": 5, "done": 2}`.
   <details><summary>Solution</summary>

   ```python
   @app.get("/todos/stats")
   def stats():
       return {"total": len(todos), "done": sum(t.done for t in todos)}
   ```
   Define it **above** `@app.get("/todos/{todo_id}")`, or "stats" will be treated as an id (422).
   </details>
2. Add `priority: int = Field(default=1, ge=1, le=3)` to todos and sort `GET /todos` by priority (3 first).
   <details><summary>Solution</summary>

   Add the field to `TodoCreate` (so `Todo` inherits it) and `priority: int | None = Field(default=None, ge=1, le=3)` to `TodoUpdate`. Then in `list_todos`:
   ```python
   result = [t for t in todos if done is None or t.done == done]
   return sorted(result, key=lambda t: t.priority, reverse=True)
   ```
   </details>
3. Add a test that creates two todos, marks one done, and checks that `/todos?done=false` returns only the other one.
   <details><summary>Solution</summary>

   ```python
   def test_filter_by_done():
       a = client.post("/todos", json={"title": "a"}).json()["id"]
       b = client.post("/todos", json={"title": "b"}).json()["id"]
       client.patch(f"/todos/{a}", json={"done": True})
       open_ids = [t["id"] for t in client.get("/todos?done=false").json()]
       assert b in open_ids and a not in open_ids
   ```
   We check "is in" rather than "equals" because other tests also add todos to the same list.
   </details>

## Check yourself
1. Why do we have both `TodoCreate` and `Todo` instead of one model?
2. What would go wrong in `update_todo` without `exclude_unset=True`?
3. Which status code does each CRUD action return on success, and why is DELETE's different?
4. Why are todos lost when the server restarts?

<details><summary>Answers</summary>

1. Clients must not set `id` or `created_at`; the server does. Separate models make it impossible for a client to send them, and the docs show each shape clearly.
2. `model_dump()` would include every field, with `None` for the ones not sent, so a PATCH of `{"done": true}` would try to set the title to `None`.
3. POST → 201 Created, GET and PATCH → 200 OK, DELETE → 204 No Content. After a delete there's nothing left to return, and 204 says exactly that.
4. They live in a Python list in memory. When the process stops, its memory is freed. A database (1.5) stores them on disk.
</details>

## Learn more (optional)
- REST APIs explained: https://www.youtube.com/results?search_query=REST+API+crud+explained+beginners
- FastAPI body updates (PATCH): https://fastapi.tiangolo.com/tutorial/body-updates/
- HTTP status codes (MDN): https://developer.mozilla.org/en-US/docs/Web/HTTP/Status

## Next
→ [1.5 · To-do API with SQLite, then PostgreSQL](../05-todo-api-with-sqlite-then-postgres)
