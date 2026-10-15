# 26 · Production vector database: Postgres + pgvector

**What you'll build:** the same "ask your documents" RAG as lesson 24, but the vectors are stored in **PostgreSQL** with the **pgvector** add-on, and similarity search is a normal SQL query.
**Time:** ~1 hour · **Builds on:** [24 · RAG: ask your documents](../24-rag-ask-your-documents) · **Needs:** an Anthropic API key and Docker Desktop

## Why this matters
Chroma is great for learning and small apps. Many companies prefer pgvector because they *already* run PostgreSQL (one of the most used databases in the world), so documents, users and vectors live in one database, with the backups, permissions and SQL their team already knows. "Postgres + pgvector" appears in a lot of AI engineer job adverts, and after this lesson you have used it.

## What you'll learn
- **PostgreSQL:** a popular, free "real" database server (lesson 03 used SQLite, a small database in a single file).
- **pgvector:** an add-on that gives Postgres a `vector` column type and distance operators, turning it into a vector database.
- **Docker:** a tool that runs ready-made software (here, Postgres with pgvector) in a box on your computer, with one command.
- **Vector search in SQL:** `ORDER BY embedding <=> question LIMIT 4` finds the 4 closest chunks.
- **HNSW index:** a shortcut structure that keeps search fast even with millions of rows.

## Before you start
- Install the Part 5 packages (once), plus the Postgres driver for Python:
  ```bash
  pip install chromadb numpy pypdf anthropic fastapi "uvicorn[standard]" python-multipart
  pip install "psycopg[binary]"
  ```
  Used here: `psycopg` (lets Python talk to Postgres), `chromadb` (only for its free embedding model, the same one as before), `anthropic` (Claude).
- Install **Docker Desktop** from https://www.docker.com/products/docker-desktop/ and start it (wait until it says it's running).
- Set your API key (full steps in the [Part 4 README](../../part-4-chatbots)):
  ```bash
  export ANTHROPIC_API_KEY=sk-ant-your-key-here        # Mac
  $env:ANTHROPIC_API_KEY="sk-ant-your-key-here"        # Windows PowerShell
  ```

## Run it
1. From the course folder (`Learning/ai-from-zero`), start the database (the first time, Docker downloads it, about 150 MB):
   ```bash
   cd part-5-rag-and-vector-databases/26-production-vector-database-postgres
   docker compose up -d
   ```
2. Ask the default question, then your own:
   ```bash
   python pg_rag.py
   python pg_rag.py "Do I need a doctor's note for sick leave?"
   ```
3. Look inside the database with plain SQL:
   ```bash
   docker compose exec db psql -U rag -c "SELECT source, left(content, 60) FROM chunks;"
   ```
4. When you're done, stop the database: `docker compose down` (your data is kept for next time; `docker compose down -v` also deletes it).

### What you should see
```
📄 expense_policy.md: 6 chunks
📄 it_security.md: 5 chunks
📄 vacation_policy.md: 6 chunks
   0.50  [expense_policy.md] ## Hotels Hotel stays are reimbursed up to 180 euros per night in majo...
   0.43  [expense_policy.md] ## Submitting expenses Submit receipts in the expense app within 30 da...
   0.39  [expense_policy.md] ## Meals While travelling, meals are reimbursed up to 60 euros per day...
   0.37  [expense_policy.md] ## Home office Each employee can claim a one-time home office allowanc...

💬 Hotels in Paris are reimbursed up to 180 euros per night [1]. Submit your receipts within 30 days of the purchase [2].
```
The numbers in front are similarity scores (1 = same meaning), straight from SQL. The two chunks that answer the question are ranked 1st and 2nd. Claude's wording will differ. With the sick-leave question, the `## Sick leave` chunk comes first with about 0.70.

Notice there are more chunks than in lesson 24 (17 instead of 8): here every paragraph is its own chunk, which is simpler.

## How it works
```
docker compose up ──► Postgres + pgvector running on your computer (port 5432)

pg_rag.py: docs/*.md ─► paragraphs ─► embeddings ─► INSERT INTO chunks
           question  ─► embedding  ─► SELECT ... ORDER BY embedding <=> question LIMIT 4 ─► Claude ─► answer
```
1. `docker-compose.yml` describes one service, `db`, using the `pgvector/pgvector:pg16` image (Postgres 16 with pgvector already installed), with user, password and database all called `rag`. `ports: "5432:5432"` makes it reachable from your computer, and the `pgdata` volume keeps the data when the box stops.
2. `psycopg.connect("postgresql://rag:rag@localhost:5432/rag", autocommit=True)` connects: user `rag`, password `rag`, on your own computer (`localhost`), port 5432, database `rag`. `autocommit=True` saves every change straight away.
3. **Set up** (3 SQL lines): `CREATE EXTENSION IF NOT EXISTS vector` switches pgvector on. The `chunks` table has an `embedding vector(384)` column, which holds exactly 384 numbers (the size our embedding model makes). The `hnsw` index with `vector_cosine_ops` makes cosine searches fast.
4. `as_vector(numbers)` turns a list of numbers into pgvector's text format, `[0.1,0.2,...]`.
5. `add_folder()` empties the table (`DELETE FROM chunks`, simple for learning), splits each `.md`/`.txt` file into paragraphs, embeds them all at once with `embed(pieces)`, and `INSERT`s one row per paragraph. `%s` are placeholders: psycopg fills them in safely, which protects you from "SQL injection".
6. `find_relevant(question)` embeds the question and runs:
   ```sql
   SELECT source, content, 1 - (embedding <=> %s::vector) AS similarity
   FROM chunks ORDER BY embedding <=> %s::vector LIMIT 4
   ```
   `<=>` is pgvector's **cosine distance** (0 = same meaning), so `1 - distance` is the similarity you know from lesson 21. `::vector` tells Postgres "treat this text as a vector".
7. The bottom block prints the 4 chunks with their scores, then asks Claude to answer using only those numbered sources, exactly like lesson 24.

## If something goes wrong
- **`psycopg.OperationalError: connection failed: ... Connection refused`** → the database isn't running. Start Docker Desktop, run `docker compose up -d` in this folder, wait ~5 seconds, and try again.
- **`failed to bind host port 0.0.0.0:5432/tcp: address already in use`** → you already have Postgres running on your computer. Either stop it, or change `"5432:5432"` to `"5433:5432"` in `docker-compose.yml`, run `docker compose up -d` again, and run the script with `DATABASE_URL=postgresql://rag:rag@localhost:5433/rag python pg_rag.py` (Mac) or set `$env:DATABASE_URL="postgresql://rag:rag@localhost:5433/rag"` first (Windows).
- **`docker: command not found`** or `Cannot connect to the Docker daemon` → Docker Desktop isn't installed or isn't started. Open it and wait until it says it's running.
- **`ModuleNotFoundError: No module named 'psycopg'`** → run `pip install "psycopg[binary]"` (with the quotes) inside your venv.
- **`❌ ANTHROPIC_API_KEY is not set`** → the search results still print, but the answer needs Claude. Set your key (see Before you start).

## Try this
1. Run the "look inside" command from step 3 of Run it, then count the rows per file with SQL:
   ```bash
   docker compose exec db psql -U rag -c "SELECT source, count(*) FROM chunks GROUP BY source;"
   ```
   <details><summary>Hint</summary>

   You should see 6, 5 and 6, matching the `📄` lines. This is the big advantage of pgvector: your vectors are ordinary rows you can count, join and filter with SQL you already know.
   </details>
2. Make `find_relevant` search **only** the expense policy, by adding a `WHERE` filter to the SQL. Then ask `How many vacation days do I get?`. What happens?
   <details><summary>Solution</summary>

   ```python
   rows = db.execute("""SELECT source, content, 1 - (embedding <=> %s::vector) AS similarity
                        FROM chunks WHERE source = 'expense_policy.md'
                        ORDER BY embedding <=> %s::vector LIMIT %s""", (q, q, how_many)).fetchall()
   ```
   Every result now comes from the expense policy, so Claude correctly says the sources don't contain the answer. This is the SQL version of Chroma's `where={...}` filter from lesson 23.
   </details>
3. Show only chunks that are a good match: add `WHERE 1 - (embedding <=> %s::vector) > 0.3` to the query (you'll need to pass `q` one more time in the tuple), and ask something unrelated like `What's the best pizza topping?`.
   <details><summary>Solution</summary>

   ```python
   rows = db.execute("""SELECT source, content, 1 - (embedding <=> %s::vector) AS similarity
                        FROM chunks WHERE 1 - (embedding <=> %s::vector) > 0.3
                        ORDER BY embedding <=> %s::vector LIMIT %s""", (q, q, q, how_many)).fetchall()
   ```
   No chunk scores above 0.3, so no sources are printed and Claude is told there's nothing to go on. Fewer, better sources means fewer made-up answers.
   </details>

## Check yourself
1. What does pgvector add to Postgres?
2. What does `ORDER BY embedding <=> %s::vector LIMIT 4` do, in plain words?
3. Why is the column `vector(384)` and not some other size?
4. Name one reason a company might pick pgvector over Chroma.

<details><summary>Answers</summary>

1. A `vector` column type for storing embeddings, distance operators like `<=>`, and indexes (like HNSW) that make vector search fast.
2. Sort all chunks by how far their meaning is from the question (closest first) and keep the top 4.
3. The embedding model makes exactly 384 numbers per text. The column must match the model's size.
4. They already run Postgres: one database for everything, with backups, permissions and SQL their team already knows, and vectors can be joined with normal tables (users, products...).
</details>

## Learn more (optional)
- [pgvector on GitHub](https://github.com/pgvector/pgvector) (the README has every operator and index option)
- [Get Docker](https://docs.docker.com/get-started/get-docker/)
- Video search: [pgvector tutorial](https://www.youtube.com/results?search_query=pgvector+postgres+tutorial)

## Next
You've finished Part 5. Now give the AI hands: → [Part 6 · 27 · AI uses a calculator](../../part-6-ai-agents-and-teams/27-ai-uses-a-calculator)
