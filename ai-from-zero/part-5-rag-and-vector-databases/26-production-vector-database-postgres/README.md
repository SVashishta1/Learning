# 26 · Production vector database: Postgres + pgvector

**What it does:** the same "ask your documents" RAG as project 24, but the vectors are stored in **PostgreSQL** with the **pgvector** add-on, and similarity search is a normal SQL query.

**Why it matters:** Chroma is great for learning and small apps. Companies often prefer pgvector because they *already* run Postgres, so documents, users and vectors live in one database with backups, permissions and SQL they know.

## Run it
1. Install Docker Desktop (https://www.docker.com/products/docker-desktop/) and start it.
2. Start the database:
   ```bash
   cd part-5-rag-and-vector-databases/26-production-vector-database-postgres
   pip install "psycopg[binary]"
   docker compose up -d
   ```
3. Ask a question:
   ```bash
   python pg_rag.py
   python pg_rag.py "Do I need a doctor's note for sick leave?"
   ```
4. When you're done: `docker compose down`

## The idea in one sentence
A column of type `vector(384)` plus the `<=>` operator ("how far apart in meaning?") turns any Postgres database into a vector database:
```sql
SELECT content FROM chunks ORDER BY embedding <=> '[0.01, -0.2, ...]' LIMIT 4;
```

## Try this
1. Look inside the database: `docker compose exec db psql -U rag -c "SELECT source, left(content, 60) FROM chunks;"`
2. Add a `WHERE source = 'expense_policy.md'` filter to the SQL in `find_relevant`, so it only searches one document.
3. Compare: which did you find easier, Chroma (project 24) or pgvector? Both are used in real jobs.
