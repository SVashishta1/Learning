# 02 · To-do list API

**What it does:** a real to-do app backend. You can add tasks, list them, mark them done and delete them.

## Run it
```bash
cd part-1-apis/02-todo-list-api
uvicorn main:app --reload
```
Open http://127.0.0.1:8000/docs and use the buttons:
1. **POST /tasks** → Try it out → body `{"title": "learn APIs"}` → Execute
2. **GET /tasks** → Execute. Your task is there.
3. **PUT /tasks/1/done** → it's marked done.
4. **DELETE /tasks/1** → gone.

## The idea in one sentence
Almost every app does just four things to data: **Create, Read, Update, Delete** (POST, GET, PUT, DELETE).

## Try this
1. Stop the server (`Ctrl + C`) and start it again. Your tasks are gone! Why? They were only in memory. The next project fixes this.
2. Add a `priority` field to `NewTask` (`priority: int = 1`) and include it in `new`.
