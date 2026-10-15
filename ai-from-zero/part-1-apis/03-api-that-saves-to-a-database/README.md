# 03 · An API that saves to a database

**What you'll build:** the to-do API from lesson 02, but tasks are stored in a database file (`tasks.db`), so they survive a restart. It can also search tasks by a word.
**Time:** ~45 min · **Builds on:** [02 · To-do list API](../02-todo-list-api) · **Needs:** nothing extra (SQLite comes with Python)

Like you're 10: lesson 02's waiter wrote orders on their hand, and washed them off every night. This waiter writes them in a notebook that stays on the shelf.

## Why this matters
Real apps must remember things after they restart: users, orders, chat histories. That's what databases are for. SQL, the language you meet here, is one of the most-used skills in tech, and in Part 5 you'll use a database (Postgres) to store the "memory" of an AI that answers questions about your documents.

## What you'll learn
- **Database**: a program that stores data safely on disk and lets you search it fast. **SQLite** keeps a whole database in one file.
- **Table, rows, columns**: like a spreadsheet. The `tasks` table has one row per task and columns `id`, `title`, `done`.
- **SQL**: the language for talking to databases, e.g. `SELECT * FROM tasks WHERE done = 1`.
- **Commit**: "save my changes to disk now".
- **Parameterised queries (`?`)**: the safe way to put user text into SQL, which blocks "SQL injection" attacks.

## Before you start
- Venv on, and this part's install line done (skip if done already):
  ```bash
  pip install fastapi "uvicorn[standard]" httpx
  ```
  `fastapi` builds the API, `uvicorn` runs it. `sqlite3` (the database) is built into Python, so there's nothing extra to install.
- No API key needed.

## Run it
1. From the course folder (`ai-from-zero`):
   ```bash
   cd part-1-apis/03-api-that-saves-to-a-database
   uvicorn main:app --reload
   ```
2. Open http://127.0.0.1:8000/docs. Use **POST /tasks** three times to add `{"title": "learn APIs"}`, `{"title": "learn SQL"}` and `{"title": "buy milk"}`. Then **PUT /tasks/{task_id}/done** with `1`.
3. Go to the terminal, **stop the server (Ctrl + C) and start it again** with the same `uvicorn` command.
4. Back in `/docs`, run **GET /tasks**. Your tasks are still there. 🎉
5. Run **GET /tasks/search** with `word` = `learn`.
6. Look in the lesson folder: there's a new file, `tasks.db`. That's your database.

### What you should see
```
POST /tasks  {"title": "learn APIs"}   →  {"id": 1, "title": "learn APIs", "done": 0}
POST /tasks  {"title": "learn SQL"}    →  {"id": 2, "title": "learn SQL", "done": 0}
POST /tasks  {"title": "buy milk"}     →  {"id": 3, "title": "buy milk", "done": 0}
PUT  /tasks/1/done                     →  {"id": 1, "done": 1}

   ...stop and restart the server...

GET  /tasks                            →  [{"id": 1, "title": "learn APIs", "done": 1}, {"id": 2, "title": "learn SQL", "done": 0}, {"id": 3, "title": "buy milk", "done": 0}]
GET  /tasks/search?word=learn          →  [{"id": 1, "title": "learn APIs", "done": 1}, {"id": 2, "title": "learn SQL", "done": 0}]
PUT  /tasks/42/done                    →  {"detail": "No task with that id"}   (code 404)
```
The key thing: **GET /tasks after the restart** still has all 3 tasks, and task 1 is still done. Notice `done` is now `0` or `1` instead of `false` / `true`: SQLite has no true/false type, so it stores 0 for false and 1 for true.

## How it works
```
POST /tasks ──▶ add_task() ──▶ INSERT INTO tasks ... ──▶ db.commit() ──▶ tasks.db (file on disk)
GET  /tasks ──▶ list_tasks() ──▶ SELECT * FROM tasks ──▶ rows ──▶ JSON
```
1. `db = sqlite3.connect("tasks.db", check_same_thread=False)` opens the database file, creating it if it doesn't exist. It's created in the folder you start the server from. `check_same_thread=False` lets FastAPI use the connection from its helper threads.
2. `db.row_factory = sqlite3.Row` makes each row readable like a dictionary, so `dict(row)` gives `{"id": 1, "title": ..., "done": 0}`.
3. `CREATE TABLE IF NOT EXISTS tasks (...)` makes the table the first time. `id INTEGER PRIMARY KEY` means SQLite hands out ids 1, 2, 3... by itself. `done INTEGER DEFAULT 0` means new tasks start as not done.
4. `list_tasks()` runs `SELECT * FROM tasks` ("give me every column of every row") and `.fetchall()` collects the rows.
5. `add_task()` runs `INSERT INTO tasks (title) VALUES (?)`. The `?` is a placeholder that sqlite fills in safely with `task.title`. Never glue user text into SQL with `+` or f-strings: someone could type SQL commands as a "title" and wipe your table. That's called **SQL injection**. `cursor.lastrowid` is the id SQLite just gave the new row. `db.commit()` saves to disk.
6. `finish_task()` runs `UPDATE tasks SET done = 1 WHERE id = ?`. `.rowcount` says how many rows changed; 0 means no such id, so it raises a 404.
7. `delete_task()` runs `DELETE FROM tasks WHERE id = ?`, same 404 check.
8. `search()` runs `SELECT * FROM tasks WHERE title LIKE ?` with `%learn%`. In SQL, `%` means "any text here", so it finds titles containing "learn" anywhere.

Compare with lesson 02: the endpoints and addresses are identical. Only the storage changed, from a Python list to SQL. That's normal in real projects too.

## If something goes wrong
- **Tasks still disappear after a restart** → you started the server from a different folder, so it opened (or created) a different `tasks.db`. Always `cd part-1-apis/03-api-that-saves-to-a-database` before running `uvicorn`.
- **`sqlite3.OperationalError: database is locked`** → another program has `tasks.db` open and is writing (for example a database viewer). Close it and try again.
- **`sqlite3.OperationalError: no such column` or `no such table` after you edited the SQL** → check spelling against the `CREATE TABLE` line. If you changed the columns in `CREATE TABLE`, stop the server, delete `tasks.db` and restart, because `IF NOT EXISTS` won't change a table that already exists.
- **Search returns `[]`** → nothing matches. `LIKE` ignores upper/lower case for English letters, but the word must appear in the title.
- **`ModuleNotFoundError: No module named 'fastapi'`** → switch your venv on and run the pip line.

## Try this
1. Look inside your database. In VS Code, install the free **SQLite Viewer** extension (Extensions icon → search "SQLite Viewer"), then click `tasks.db`. You'll see your table like a spreadsheet.
2. Add an endpoint `GET /tasks/done` that returns only finished tasks, using `SELECT * FROM tasks WHERE done = 1`.
3. Add `PUT /tasks/{task_id}` that renames a task. It takes a `NewTask` body and runs `UPDATE tasks SET title = ? WHERE id = ?`.

<details><summary>Hints and solutions</summary>

1. No code needed. Add a task in `/docs`, then reopen the viewer tab to see the new row.
2. Copy `list_tasks()` and change the address and SQL:
   ```python
   @app.get("/tasks/done")
   def done_tasks():
       rows = db.execute("SELECT * FROM tasks WHERE done = 1").fetchall()
       return [dict(row) for row in rows]
   ```
3. Mix `add_task()` (it takes a body) and `finish_task()` (it updates by id):
   ```python
   @app.put("/tasks/{task_id}")
   def rename_task(task_id: int, task: NewTask):
       changed = db.execute("UPDATE tasks SET title = ? WHERE id = ?", (task.title, task_id)).rowcount
       db.commit()
       if changed == 0:
           raise HTTPException(404, "No task with that id")
       return {"id": task_id, "title": task.title}
   ```
   The order of values in the tuple must match the order of the `?` marks.
</details>

## Check yourself
1. Why do tasks survive a restart now, when they didn't in lesson 02?
2. What happens if you forget `db.commit()` after an `INSERT`?
3. Why is `"... WHERE title LIKE ?", (f"%{word}%",)` safe, but `f"... WHERE title LIKE '%{word}%'"` dangerous?
4. What does `WHERE id = ?` do in the `UPDATE` and `DELETE` statements?

<details><summary>Answers</summary>

1. They're written to a file on disk (`tasks.db`), not kept in memory. Files stay when a program stops.
2. The change may never be saved to disk, so it can be lost when the server stops.
3. With `?`, sqlite treats the user's text strictly as data. Glued into the SQL string, the text becomes part of the command, so a user could inject their own SQL (like deleting the table).
4. It picks which rows to change: only the row whose id matches. Without a `WHERE`, `UPDATE` and `DELETE` would affect every row in the table.
</details>

## Learn more (optional)
- SQLite in Python (official docs, with a tutorial): https://docs.python.org/3/library/sqlite3.html
- Interactive SQL lessons in your browser: https://sqlbolt.com/
- Video: search YouTube for "SQL in 100 seconds" or "SQL for beginners".

## Next
→ [04 · Your code calls another API](../04-your-code-calls-another-api)
