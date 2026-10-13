# 1.5 · To-do API + database: SQLite, then PostgreSQL

**What you build:** the same to-do API, but tasks are saved in a **database**, so they survive restarts. You start with SQLite (a single file) and then switch to PostgreSQL (a real database server) by changing **one line of configuration**.
**Like you're 10:** project 1.4 wrote tasks on a whiteboard (wiped when the lights go off). Now we write them in a notebook kept in a locker.

## Part A: SQLite (zero setup)
```bash
cd level-1-apis/05-todo-api-with-sqlite-then-postgres
pip install -r requirements.txt
uvicorn main:app --reload
```
Add some todos at http://127.0.0.1:8000/docs, stop the server (`Ctrl+C`), start it again. **Your todos are still there.** A file `todos.db` appeared; that's your database.

Peek inside (optional): install "SQLite Viewer" in VS Code and open `todos.db`.

## Part B: PostgreSQL (what companies use)
1. Install Docker Desktop: https://www.docker.com/products/docker-desktop/
2. Start Postgres: `docker compose up -d`
3. Point the app at it and run:
   ```bash
   # macOS/Linux
   export DATABASE_URL=postgresql+psycopg://todo:todo@localhost:5432/todos
   # Windows PowerShell
   $env:DATABASE_URL="postgresql+psycopg://todo:todo@localhost:5432/todos"
   uvicorn main:app --reload
   ```
4. Same API, different database. Stop Postgres later with `docker compose down`.

Test: `pytest -v`

## Key ideas
- **Table** = a spreadsheet; **row** = one todo; **column** = a field (title, done).
- **ORM (SQLAlchemy)** lets you write Python (`select(TodoRow).where(...)`) instead of raw SQL strings. It also protects you from SQL injection.
- **Dependency injection:** `db: Session = Depends(get_db)` gives each request its own DB connection and closes it afterwards.
- **Environment variables** (`DATABASE_URL`) keep configuration *outside* the code. This matters a lot when you deploy (1.7) and when you store API keys (Level 7).

## Your turn
1. Add a `priority` column. (You'll need to delete `todos.db` because the table already exists. Real projects use **Alembic migrations** for this; look it up!)
2. Add `GET /todos/search?q=milk` using `TodoRow.title.contains(q)`.
3. Write the raw SQL that `list_todos(done=True)` runs. (Hint: `create_engine(..., echo=True)` prints it.)

## Watch
- SQL in 100 seconds (Fireship): https://www.youtube.com/results?search_query=fireship+sql+explained+in+100+seconds
- FastAPI + SQL databases: https://fastapi.tiangolo.com/tutorial/sql-databases/
