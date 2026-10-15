# 02 · To-do list API

**What you'll build:** the "back end" of a real to-do app: an API where you can add tasks, list them, mark them done and delete them.
**Time:** ~40 min · **Builds on:** [01 · Your first API](../01-your-first-api) · **Needs:** nothing extra

Like you're 10: last time the waiter could only bring things. Now the waiter also takes orders, changes them and cancels them.

## Why this matters
Almost every app (shops, social media, banking, and the chat history in AI apps) does just four things to data: **Create, Read, Update, Delete**, known as **CRUD**. Once you can build a CRUD API, you can build the back end of most apps. Later in the course, the chatbot and RAG projects use the same patterns to store conversations and documents.

## What you'll learn
- **CRUD**: Create, Read, Update, Delete, the four basic things you do to data.
- **HTTP methods**: the "verb" of a request. `POST` = create, `GET` = read, `PUT` = update, `DELETE` = delete.
- **Request body**: data sent inside a request (like `{"title": "learn APIs"}`), not in the address.
- **Pydantic model**: a small class that describes what the body must look like, so bad data is rejected automatically.
- **Status codes**: numbers that say how it went. `200` = OK, `404` = not found, `422` = your input is wrong.

## Before you start
- Venv on, and this part's install line done (skip it if you did it in lesson 01):
  ```bash
  pip install fastapi "uvicorn[standard]" httpx
  ```
  `fastapi` builds the API (and brings `pydantic`, which checks the body), `uvicorn` runs it.
- No API key needed.

## Run it
1. From the course folder (`ai-from-zero`):
   ```bash
   cd part-1-apis/02-todo-list-api
   uvicorn main:app --reload
   ```
   (If you're still inside `01-your-first-api`, go back to the course folder first with `cd ../..`.)
2. Open http://127.0.0.1:8000/docs and use the buttons. For each one: click it, then **Try it out**, then **Execute**.
   1. **POST /tasks** → in the body box, replace the example with `{"title": "learn APIs"}` → Execute. Do it again with `{"title": "buy milk"}`.
   2. **GET /tasks** → Execute. Both tasks are listed.
   3. **PUT /tasks/{task_id}/done** → type `1` in **task_id** → Execute. Task 1 is now done.
   4. **DELETE /tasks/{task_id}** → type `2` → Execute. "buy milk" is gone.
   5. **DELETE /tasks/{task_id}** again with `99` → you get a 404 error.
3. Stop the server with **Ctrl + C** when you're done.

### What you should see
The **Response body** box under each Execute button shows:
```
POST /tasks  {"title": "learn APIs"}  →  {"id": 1, "title": "learn APIs", "done": false}
POST /tasks  {"title": "buy milk"}    →  {"id": 2, "title": "buy milk", "done": false}
GET  /tasks                           →  [{"id": 1, "title": "learn APIs", "done": false}, {"id": 2, "title": "buy milk", "done": false}]
PUT  /tasks/1/done                    →  {"id": 1, "title": "learn APIs", "done": true}
DELETE /tasks/2                       →  {"deleted": 2}
DELETE /tasks/99                      →  {"detail": "No task with that id"}      (code 404)
POST /tasks  {}                       →  {"detail": [{"type": "missing", "loc": ["body", "title"], "msg": "Field required", ...}]}   (code 422)
```
Look at the **Code** column next to each response: 200 for success, 404 when the task doesn't exist, 422 when the body is missing its `title`. The terminal logs each request, e.g. `"DELETE /tasks/99 HTTP/1.1" 404 Not Found`.

## How it works
```
POST /tasks {"title": ...} ──▶ add_task()    ──▶ tasks.append(...)       (Create)
GET  /tasks                ──▶ list_tasks()  ──▶ return tasks            (Read)
PUT  /tasks/1/done         ──▶ finish_task() ──▶ task["done"] = True     (Update)
DELETE /tasks/1            ──▶ delete_task() ──▶ tasks.remove(task)      (Delete)
```
1. `tasks = []` is the "storage": a plain Python list that lives in the computer's memory. `next_id = 1` is the number the next task will get.
2. `class NewTask(BaseModel): title: str` is a **Pydantic model**. It says "a new task must be JSON with a `title` that is text". If the body doesn't match, FastAPI answers `422` and your function never runs.
3. `list_tasks()` (`@app.get("/tasks")`) simply returns the list. FastAPI turns it into JSON.
4. `add_task(task: NewTask)` (`@app.post("/tasks")`): because the parameter's type is a Pydantic model, FastAPI reads it from the **request body**. The function builds a dictionary with an id, adds it to `tasks`, and adds 1 to `next_id`. `global next_id` is needed because the function changes a variable that lives outside it.
5. `finish_task(task_id: int)` (`@app.put("/tasks/{task_id}/done")`) loops through the tasks, finds the matching id and sets `"done"` to `True`.
6. `delete_task(task_id: int)` (`@app.delete(...)`) finds the task and removes it from the list.
7. If no task matches, both raise `HTTPException(status_code=404, ...)`. "Raise" means "stop here and send this error back". `404` is the web's code for "not found".

Why can't you just type these addresses in the browser like in lesson 01? A browser's address bar only sends `GET` requests. The `/docs` page (or code, as you'll write in lesson 04) can send `POST`, `PUT` and `DELETE` too.

## If something goes wrong
- **Your tasks vanished** → you restarted the server, or saved the file (which makes `--reload` restart it). Tasks live in memory, which is wiped on every restart. Lesson 03 fixes this.
- **`422 Unprocessable Content` when adding a task** → the body isn't valid JSON with a `title`. Use double quotes: `{"title": "learn APIs"}`, not `{'title': 'learn APIs'}` or `{title: learn APIs}`.
- **`404 No task with that id`** → that id doesn't exist (yet, or any more). Run **GET /tasks** to see which ids exist. Ids are never reused, even after a delete.
- **`address already in use`** → the lesson 01 server is still running in another terminal. Stop it with Ctrl + C, or run this one with `--port 8001`.
- **`Could not import module "main"`** → you're in the wrong folder. Go to `part-1-apis/02-todo-list-api` first.

## Try this
1. Add two tasks, then stop the server (**Ctrl + C**) and start it again. Run **GET /tasks**. Where did your tasks go, and why?
2. Add a `priority` field to `NewTask` (`priority: int = 1`) and include it in the `new` dictionary. Add a task with `{"title": "pay rent", "priority": 3}` and one without a priority.
3. Add `GET /tasks/{task_id}` that returns one task, or a 404 if it doesn't exist.

<details><summary>Hints and solutions</summary>

1. The list is empty. `tasks = []` runs again every time the server starts, and memory is wiped when a program stops.
2. Change the class and one line in `add_task`:
   ```python
   class NewTask(BaseModel):
       title: str
       priority: int = 1          # "= 1" makes it optional, with 1 as the default
   ```
   ```python
   new = {"id": next_id, "title": task.title, "done": False, "priority": task.priority}
   ```
   The task without a priority gets `"priority": 1`.
3. Add at the end of the file (it's `finish_task` without the "change" line):
   ```python
   @app.get("/tasks/{task_id}")
   def get_task(task_id: int):
       for task in tasks:
           if task["id"] == task_id:
               return task
       raise HTTPException(status_code=404, detail="No task with that id")
   ```
</details>

## Check yourself
1. Which HTTP method would you use to (a) see all tasks, (b) add a task, (c) mark a task done?
2. What does `class NewTask(BaseModel)` protect your code from?
3. You get status code `404`. What does that mean, and what's one way it can happen here?
4. Why do tasks disappear when the server restarts?

<details><summary>Answers</summary>

1. (a) `GET`, (b) `POST`, (c) `PUT`.
2. From bad input: a body without a `title`, or a title that isn't text, is rejected with a 422 before your function runs.
3. "Not found". It happens when you ask to finish or delete an id that doesn't exist, like 99.
4. They're kept in a Python list in memory. When the program stops, its memory is cleared, and the list starts empty again.
</details>

## Learn more (optional)
- FastAPI tutorial, "Request Body": https://fastapi.tiangolo.com/tutorial/body/
- HTTP request methods (MDN): https://developer.mozilla.org/en-US/docs/Web/HTTP/Methods
- HTTP status codes (MDN): https://developer.mozilla.org/en-US/docs/Web/HTTP/Status
- Video: search YouTube for "CRUD API explained" or "HTTP methods GET POST PUT DELETE".

## Next
→ [03 · An API that saves to a database](../03-api-that-saves-to-a-database)
