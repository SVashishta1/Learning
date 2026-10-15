# 1.5 · To-do API with SQLite, then PostgreSQL

**What you'll build:** the same to-do API as 1.4, but tasks are saved in a **database**, so they survive restarts. You start with SQLite (a single file) and then switch to PostgreSQL (a real database server) by changing **one setting**, `DATABASE_URL`.
**Like you're 10:** project 1.4 wrote tasks on a whiteboard (wiped when the lights go off). Now we write them in a notebook kept in a locker.
**Time:** ~2 h · **Builds on:** [1.4 · To-do API: CRUD in memory](../04-todo-api-crud-in-memory) · **Needs:** nothing for Part A; Docker Desktop **or** an installed PostgreSQL for Part B

## Why this matters
Every real app keeps its data in a database: users, orders, chat history, documents. PostgreSQL is the most popular choice at companies and it powers many AI products (with the `pgvector` extension it even stores embeddings for RAG, which you'll meet in Level 7). Learning to talk to it through an ORM, and to configure it with an environment variable, is a core backend skill.

## What you'll learn
- **Database, table, row, column:** a table is like a spreadsheet; each row is one todo; each column is a field (`title`, `done`).
- **ORM (SQLAlchemy):** you write Python classes and queries; SQLAlchemy writes the SQL and protects you from SQL injection.
- **Sessions and dependency injection:** `db: Session = Depends(get_db)` gives each request its own database session and closes it afterwards.
- **Environment variables:** `DATABASE_URL` keeps configuration *outside* the code, so the same code runs with SQLite on your laptop and Postgres in the cloud.
- **Persistence:** data written to disk survives restarts; memory doesn't.

## Before you start
```bash
cd level-1-apis/05-todo-api-with-sqlite-then-postgres
pip install -r requirements.txt
```
- `fastapi`, `uvicorn[standard]`: web framework and server.
- `sqlalchemy`: the ORM.
- `psycopg[binary]`: the PostgreSQL driver (version 3). Only used in Part B.
- `pytest`, `httpx`, `httpx2`: to run the tests.

No API key needed. For Part B you need **one** of these:
- **Docker Desktop** (easiest, nothing else to configure): https://www.docker.com/products/docker-desktop/
- **PostgreSQL 16 installed directly**: https://www.postgresql.org/download/ (macOS users can also use https://postgresapp.com/).

## Run it
### Part A: SQLite (zero setup)
1. Start the server: `uvicorn main:app --reload`
2. Add a todo at http://127.0.0.1:8000/docs (`POST /todos`).
3. Stop the server (`Ctrl+C`) and start it again. GET `/todos`: **your todo is still there.**
4. A file `todos.db` appeared in the folder. That's your whole database. (Optional: install the "SQLite Viewer" extension in VS Code and click it.)
5. Run the tests: `pytest -v`

### Part B: PostgreSQL (what companies use)
1. Start a Postgres server, either way:
   - **With Docker:** `docker compose up -d` (uses `docker-compose.yml` in this folder; the first run downloads the Postgres image).
   - **With installed Postgres:** create the same user and database the Docker version creates:
     ```bash
     psql -U postgres -c "CREATE USER todo WITH PASSWORD 'todo';"
     psql -U postgres -c "CREATE DATABASE todos OWNER todo;"
     ```
     (On Linux you may need `sudo -u postgres psql -c "..."` instead.)
2. Point the app at it and start it:
   ```bash
   # macOS/Linux
   export DATABASE_URL=postgresql+psycopg://todo:todo@localhost:5432/todos
   uvicorn main:app --reload
   ```
   ```powershell
   # Windows PowerShell
   $env:DATABASE_URL="postgresql+psycopg://todo:todo@localhost:5432/todos"
   uvicorn main:app --reload
   ```
3. Add todos in `/docs`. Same API, different database. Look inside with SQL:
   ```bash
   docker compose exec db psql -U todo -d todos -c "SELECT * FROM todos;"     # Docker
   psql -h localhost -U todo -d todos -c "SELECT * FROM todos;"               # installed Postgres (password: todo)
   ```
4. Optional: run the tests against Postgres too: `TEST_DATABASE_URL=postgresql+psycopg://todo:todo@localhost:5432/todos pytest -v` (PowerShell: set `$env:TEST_DATABASE_URL="..."` first, then `pytest -v`).
5. When you're done: `docker compose down` (add `-v` to also delete the stored data). For installed Postgres, just leave it running or stop it from your system's services.

### What you should see
Part A, creating a todo, restarting the server, then `GET /todos`:
```
{"title":"buy milk","done":false,"id":1,"created_at":"2026-10-15T03:55:15.431616"}
... Ctrl+C, uvicorn main:app --reload again ...
[{"title":"buy milk","done":false,"id":1,"created_at":"2026-10-15T03:55:15.431616"}]
```
Part B, the same data seen from inside PostgreSQL:
```
 id |       title        | done |          created_at
----+--------------------+------+-------------------------------
  1 | stored in postgres | f    | 2026-10-15 03:55:23.683365+00
(1 row)
```
The todo survived the restart. In Postgres, `created_at` carries its time zone (`+00` = UTC); SQLite doesn't store time zones, which is why the SQLite reply has no `Z` at the end.

## How it works
```
request ──► FastAPI route ──► Depends(get_db) opens a Session ──► SQLAlchemy writes SQL ──► SQLite file / Postgres server
                                                        ◄── rows ◄────────────────────────┘
```
1. **`database.py`** reads `DATABASE_URL` with `os.getenv(...)`, falling back to `sqlite:///./todos.db` (a file in the folder you start the server from). `create_engine()` makes the connection pool. SQLite needs `check_same_thread=False` because FastAPI may use the connection from different threads. `SessionLocal` is a factory for sessions (one conversation with the database).
2. **`get_db()`** is a FastAPI *dependency*. It opens a session, `yield`s it to the route, and the `finally` block closes it even if the route crashed.
3. **`models.py`** defines `TodoRow(Base)`: `__tablename__ = "todos"` names the table, and each `mapped_column(...)` is a column (`Integer` primary key, `String(200)`, `Boolean`, `DateTime(timezone=True)` with a default of "now in UTC").
4. **`main.py`** first calls `Base.metadata.create_all(bind=engine)`: "create any table that doesn't exist yet". It never changes an existing table.
5. The Pydantic models are the same as 1.4. `Todo` adds `model_config = ConfigDict(from_attributes=True)` so Pydantic can read a `TodoRow` object directly.
6. The routes mirror 1.4 but talk to the database:
   - `create_todo`: `db.add(row)` → `db.commit()` (save for real) → `db.refresh(row)` (read back the id the database chose).
   - `list_todos`: `select(TodoRow).order_by(TodoRow.id)` plus `.where(TodoRow.done == done)` when filtering. SQLAlchemy turns this into `SELECT ... FROM todos WHERE todos.done = ...`.
   - `get_todo` / `find`: `db.get(TodoRow, todo_id)` looks up by primary key, 404 if `None`.
   - `update_todo`: same `exclude_unset=True, exclude_none=True` trick as 1.4, then `commit`.
   - `delete_todo`: `db.delete(row)` then `commit`.
7. **`test_main.py`** sets `DATABASE_URL` to a throwaway SQLite file in a temp folder *before* importing `main`, so tests never touch your real `todos.db`.

## If something goes wrong
- **`ModuleNotFoundError: No module named 'psycopg2'`** or **`Can't load plugin: sqlalchemy.dialects:postgres`** → write the URL as `postgresql+psycopg://...`. Plain `postgres://` isn't understood, and older SQLAlchemy (2.0) picks the psycopg2 driver for `postgresql://`; `+psycopg` always picks psycopg 3, the one we installed.
- **`connection to server at "localhost" ... port 5432 failed: Connection refused`** → Postgres isn't running. Run `docker compose up -d` (and check `docker ps`), or start your installed Postgres.
- **`password authentication failed for user "todo"`** → the user/password in `DATABASE_URL` doesn't match the database. With Docker they're `todo`/`todo`; with installed Postgres, re-run the `CREATE USER` step.
- **`Bind for 0.0.0.0:5432 failed: port is already allocated`** (Docker) → another Postgres already uses port 5432. Stop it, or change the compose file to `"5433:5432"` and use `localhost:5433` in the URL.
- **You added a column but get `no such column` / `column ... does not exist`** → `create_all` doesn't change existing tables. Delete `todos.db` (SQLite) or run `docker compose down -v` (Postgres) to start fresh. Real projects use migrations (Alembic) instead.

## Try this
1. Add `GET /todos/search?q=milk` that returns todos whose title contains `q`.
   <details><summary>Solution</summary>

   ```python
   @app.get("/todos/search", response_model=list[Todo])
   def search_todos(q: str, db: Session = Depends(get_db)):
       return db.scalars(select(TodoRow).where(TodoRow.title.contains(q))).all()
   ```
   Put it **above** `/todos/{todo_id}`. SQLAlchemy turns `.contains(q)` into `title LIKE '%' || ? || '%'`, with `q` passed safely as a parameter.
   </details>
2. See the SQL that `list_todos(done=True)` runs.
   <details><summary>Solution</summary>

   In `database.py`, change to `create_engine(DATABASE_URL, connect_args=connect_args, echo=True)`, restart, and open `/todos?done=true`. The terminal prints:
   ```
   SELECT todos.id, todos.title, todos.done, todos.created_at
   FROM todos
   WHERE todos.done = 1 ORDER BY todos.id
   ```
   (SQLite stores `True` as `1`; on Postgres you'll see `WHERE todos.done = true`.)
   </details>
3. Add a `priority` column (1 to 3, default 1) and return todos sorted by priority, highest first.
   <details><summary>Solution</summary>

   In `models.py`: `priority: Mapped[int] = mapped_column(Integer, default=1)`. In `main.py`, add `priority: int = Field(default=1, ge=1, le=3)` to `TodoCreate`, `priority: int | None = Field(default=None, ge=1, le=3)` to `TodoUpdate`, and change the query to `select(TodoRow).order_by(TodoRow.priority.desc(), TodoRow.id)`.
   Then delete `todos.db` (or `docker compose down -v`), because the existing table has no `priority` column. Look up **Alembic** to see how real projects change tables without deleting data.
   </details>

## Check yourself
1. Why do todos survive a restart now, but didn't in 1.4?
2. What is the only thing you change to switch from SQLite to PostgreSQL, and why is it not in the code?
3. What do `db.commit()` and `db.refresh(row)` each do in `create_todo`?
4. Why does `test_main.py` set `DATABASE_URL` before `from main import app`?

<details><summary>Answers</summary>

1. They are written to a database on disk (a file for SQLite, the server's storage for Postgres), not kept in the program's memory.
2. The `DATABASE_URL` environment variable. Configuration that differs between laptop, tests and cloud belongs outside the code, so the same code runs everywhere and secrets (passwords) never get committed.
3. `commit()` makes the change permanent in the database. `refresh(row)` reloads the row so Python sees values the database filled in, like the new `id`.
4. `database.py` reads `DATABASE_URL` when it's imported (and `main` imports it). Setting it first makes the app use a throwaway test database.
</details>

## Learn more (optional)
- SQL in 100 seconds (Fireship): https://www.youtube.com/results?search_query=fireship+sql+explained+in+100+seconds
- FastAPI + SQL databases: https://fastapi.tiangolo.com/tutorial/sql-databases/
- SQLAlchemy 2.0 ORM quickstart: https://docs.sqlalchemy.org/en/20/orm/quickstart.html
- PostgreSQL tutorial for beginners: https://www.youtube.com/results?search_query=postgresql+tutorial+for+beginners

## Next
→ [1.6 · Login API: hashed passwords + JWT](../06-login-api-hashed-passwords-and-jwt)
