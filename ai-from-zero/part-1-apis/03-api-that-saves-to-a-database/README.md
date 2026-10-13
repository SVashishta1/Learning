# 03 · An API that saves to a database

**What it does:** the to-do API from 02, but tasks are stored in a database file (`tasks.db`), so they're still there after a restart. It adds a search, too.

## Run it
```bash
cd part-1-apis/03-api-that-saves-to-a-database
uvicorn main:app --reload
```
At http://127.0.0.1:8000/docs, add a few tasks, then **stop and restart the server**. They're still there. 🎉
Try **GET /tasks/search** with `word = learn`.

## The idea in one sentence
A database is a super-organised spreadsheet: a **table** (`tasks`) has **rows** (one per task) and **columns** (id, title, done), and you talk to it in **SQL** (`SELECT * FROM tasks`).

## Try this
1. Install the free "SQLite Viewer" extension in VS Code and open `tasks.db` to see your table.
2. Add an endpoint `GET /tasks/done` that runs `SELECT * FROM tasks WHERE done = 1`.
3. Delete `tasks.db` and restart. A fresh, empty database is created.
