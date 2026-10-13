# 23 · Your first vector database (Chroma)

**What it does:** stores 6 recipes in **Chroma**, a real vector database. It searches them by meaning ("something sweet" finds the lava cake), filters by labels (only vegan, under 20 minutes), and updates and deletes records. Everything is saved to disk.

## Run it
```bash
cd part-5-rag-and-vector-databases/23-your-first-vector-database-chroma
python vector_db.py
```

## The idea in one sentence
A vector database = a normal database (ids, labels, update, delete) **plus** search by meaning, with the embeddings handled for you.

| Normal database (project 03) | Vector database |
|---|---|
| `WHERE title LIKE '%cake%'` (exact words) | `query("something sweet")` (meaning) |
| table | collection |
| row | document + its embedding |
| columns | metadata (labels you can filter on) |

## Try this
1. Add 5 recipes of your own with an extra label, like `"spicy": True`, and filter on it.
2. Delete the `chroma_data` folder to start fresh.
3. Search for "breakfast". Which recipe wins, and why?
