# 23 · Your first vector database (Chroma)

**What you'll build:** a small recipe database in **Chroma**, a real vector database. It searches by meaning ("something sweet" finds the lava cake), filters by labels (only vegan, under 20 minutes), updates and deletes records, and saves everything to disk.
**Time:** ~45 min · **Builds on:** [22 · Search by meaning](../22-search-by-meaning) and the database idea from [03 · An API that saves to a database](../../part-1-apis/03-api-that-saves-to-a-database) · **Needs:** nothing extra (no API key)

## Why this matters
In lesson 22 you did vector search by hand, with everything held in memory. Real apps use a **vector database** that stores the embeddings on disk, keeps them up to date and searches them fast. Chroma, Pinecone, Weaviate, Qdrant and pgvector (lesson 26) all work the way you'll see here, and "experience with vector databases" appears in most AI engineer job adverts.

## What you'll learn
- **Vector database:** a normal database (ids, labels, update, delete) **plus** search by meaning, with the embeddings made for you.
- **Collection:** a group of related records, like a table in a normal database.
- **Metadata filter:** combine "close in meaning" with exact rules like `diet = vegan` or `minutes < 20`.
- **Upsert:** "insert, or replace if this id already exists", so re-running your code never makes duplicates.
- **Persistence:** the data lives in a folder on disk and is still there next time.

## Before you start
- Install the Part 5 packages (once):
  ```bash
  pip install chromadb numpy pypdf anthropic fastapi "uvicorn[standard]" python-multipart
  ```
  This lesson only uses `chromadb`, the vector database.
- No API key needed.

## Run it
1. From the course folder (`Learning/ai-from-zero`), with your venv switched on:
   ```bash
   cd part-5-rag-and-vector-databases/23-your-first-vector-database-chroma
   python vector_db.py
   ```
2. Run it a second time and compare the first line.

### What you should see
```
Already saved on disk from your last run: 0 recipes.
After adding: the database holds 6 recipes.

🔎 'something sweet for dessert'
   0.50  Chocolate lava cake with a gooey molten centre  {'diet': 'vegetarian', 'minutes': 30}
   0.43  Mango smoothie with yogurt and honey  {'diet': 'vegetarian', 'minutes': 5}

🔎 'a warm dinner' but only vegan
   0.24  Spicy black bean tacos with avocado and lime  {'diet': 'vegan', 'minutes': 15}
   0.14  Vegan chickpea curry with coconut milk and spinach  {'diet': 'vegan', 'minutes': 35}

🔎 'healthy food' ready in under 20 minutes
   0.36  Mango smoothie with yogurt and honey  {'diet': 'vegetarian', 'minutes': 5}
   0.29  Spicy black bean tacos with avocado and lime  {'diet': 'vegan', 'minutes': 15}

After one update and one delete: 5 recipes. Run me again: the first line will show they were saved on disk.
```
On the **second** run the first line says `Already saved on disk from your last run: 5 recipes.`: the database remembered. (Then `upsert` puts all 6 original recipes back, so the rest looks the same.)

Look at the second search: only vegan recipes appear, even though the salmon or carbonara might be "closer" to "a warm dinner". The filter is applied first, then the meaning search. A new folder, `chroma_data`, has appeared: that is your database. (The order of the labels inside `{...}` may differ; that doesn't matter.)

## How it works
| Normal database (lesson 03) | Vector database |
|---|---|
| `WHERE title LIKE '%cake%'` (exact words) | `query(query_texts=["something sweet"])` (meaning) |
| table | collection |
| row | document + its embedding |
| columns | metadata (labels you can filter on) |

1. `chromadb.PersistentClient(path="chroma_data")` opens (or creates) a database stored in the `chroma_data` folder.
2. `get_or_create_collection("recipes", configuration={"hnsw": {"space": "cosine"}})` opens the `recipes` collection, creating it the first time. `"cosine"` tells Chroma to compare meanings with cosine similarity, like you did in lessons 21–22. (HNSW is the name of the clever index that makes search fast.)
3. `recipes.upsert(ids=..., documents=..., metadatas=...)` adds 6 recipes. Each needs a unique **id** (`"r1"`...), the **text**, and **labels**. Chroma embeds the texts for you with the same free model as lesson 21.
4. `show(title, results)` prints the results. Chroma returns a **distance** (0 = identical), so `1 - distance` turns it back into the similarity score you know. Results come back as lists inside lists (`[0]`), because you can send several questions at once.
5. The three `recipes.query(...)` calls:
   - `query_texts=[...]`, `n_results=2`: the 2 closest recipes by meaning.
   - `where={"diet": "vegan"}`: only records whose label matches exactly.
   - `where={"minutes": {"$lt": 20}}`: `$lt` means "less than". There are also `$gt` (greater than), `$lte`, `$gte`, `$ne` (not equal) and `$in`.
6. `recipes.update(...)` changes recipe r5 (Chroma re-embeds the new text) and `recipes.delete(ids=["r3"])` removes the lava cake. `count()` drops to 5.

## If something goes wrong
- **`ModuleNotFoundError: No module named 'chromadb'`** → switch on your venv and run the `pip install` line again.
- **`TypeError` or "unexpected keyword argument 'configuration'"** → you have an old Chroma version. Run `pip install -U chromadb`, then delete the `chroma_data` folder and run again.
- **Strange old results, or an error after you changed the code a lot** → the database still holds data from earlier runs. Delete the `chroma_data` folder to start fresh. Nothing else depends on it.
- **A filter returns fewer results than `n_results`** → only that many records match the filter. That's correct, not a bug.

## Try this
1. Search for "breakfast". Which recipe wins, and why? Add the line below the other searches:
   ```python
   show("🔎 'breakfast'", recipes.query(query_texts=["breakfast"], n_results=2))
   ```
   <details><summary>Hint</summary>

   The carbonara wins (about 0.40), probably because it mentions **eggs**, which the model links with breakfast. The smoothie, a more natural breakfast, scores lower. Search by meaning is good, not perfect, and the words you put in your documents matter.
   </details>
2. Add a recipe with an extra label, `"spicy": True`, and search with `where={"spicy": True}`.
   <details><summary>Solution</summary>

   ```python
   recipes.upsert(ids=["r7"], documents=["Red lentil dal with garlic, chilli and fresh ginger"],
                  metadatas=[{"diet": "vegan", "minutes": 30, "spicy": True}])
   show("🔎 'something hot' (spicy only)", recipes.query(query_texts=["something hot"], n_results=2, where={"spicy": True}))
   ```
   Only r7 comes back: no other recipe has the `spicy` label.
   </details>
3. Find **vegan** recipes ready in **20 minutes or less**, with one query.
   <details><summary>Solution</summary>

   Combine two rules with `$and`:
   ```python
   show("🔎 quick vegan", recipes.query(query_texts=["a quick meal"], n_results=2,
                                        where={"$and": [{"diet": "vegan"}, {"minutes": {"$lte": 20}}]}))
   ```
   The mango smoothie (vegan since the update) and the black bean tacos (15 minutes) come back. The curry (35 minutes) and the non-vegan recipes are filtered out.
   </details>

## Check yourself
1. What does Chroma do for you that you did by hand in lesson 22?
2. What's the difference between `query_texts` and `where`?
3. Why does the code use `upsert` instead of `add`?
4. You delete the `chroma_data` folder. What happens on the next run?

<details><summary>Answers</summary>

1. It makes and stores the embeddings, saves them to disk, compares the question with every record, and sorts the results. It also adds labels, filters, update and delete.
2. `query_texts` searches by meaning (closest first). `where` is an exact rule on the labels, like a normal database filter. You can use both together.
3. `upsert` replaces a record if its id already exists, so running the file again doesn't create duplicates and always stores your latest text. `add` skips ids that already exist, so a changed recipe text would be silently ignored.
4. The first line says 0 recipes, and a new, empty database is created and filled again.
</details>

## Learn more (optional)
- [Chroma documentation](https://docs.trychroma.com/)
- Video search: [vector databases explained](https://www.youtube.com/results?search_query=vector+databases+explained)

## Next
→ [24 · RAG: ask your documents](../24-rag-ask-your-documents)
