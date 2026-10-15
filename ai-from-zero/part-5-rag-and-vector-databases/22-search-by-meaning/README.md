# 22 · Search by meaning

**What you'll build:** a mini search engine for a shop's help-centre FAQ. Typing "I want my money back" finds *"How can I get a refund for my order?"* even though no words match.
**Time:** ~30 min · **Builds on:** [21 · What is an embedding?](../21-what-is-an-embedding) · **Needs:** nothing extra (no API key)

## Why this matters
This is **vector search**, the "R" (retrieval) in RAG. Help centres, shop search bars, "similar products" and every "chat with your documents" app work this way. Building it by hand once, in 20 lines, means a vector database (next lesson) will never feel like magic.

## What you'll learn
- **Vector search:** turn every document into numbers once, turn the question into numbers, and return the documents whose numbers are closest.
- **Index once, search many times:** the slow part (embedding all documents) happens once; each search only embeds one short question.
- **Ranking:** sort every document by its similarity score and keep the top few.
- **Command-line arguments:** `sys.argv` lets you type your own search after `python search.py`.

## Before you start
- Install the Part 5 packages (once):
  ```bash
  pip install chromadb numpy pypdf anthropic fastapi "uvicorn[standard]" python-multipart
  ```
  This lesson uses `chromadb` (for its free embedding model) and `numpy` (fast maths on lists of numbers).
- No API key needed.

## Run it
1. From the course folder (`Learning/ai-from-zero`), with your venv switched on:
   ```bash
   cd part-5-rag-and-vector-databases/22-search-by-meaning
   python search.py
   ```
2. Search for anything you like. Put your question in quotes:
   ```bash
   python search.py "can you deliver to Japan?"
   ```

### What you should see
```
🔎 'I want my money back'
   0.55  How can I get a refund for my order?
   0.37  How do I cancel my subscription?

🔎 'I forgot my login'
   0.61  How do I reset my password?
   0.30  How do I cancel my subscription?

🔎 'the box came broken'
   0.52  What should I do if my package arrives damaged?
   0.32  How do I contact customer support?

🔎 'stop charging me every month'
   0.46  How do I cancel my subscription?
   0.22  How can I get a refund for my order?
```
And for `python search.py "can you deliver to Japan?"`:
```
🔎 'can you deliver to Japan?'
   0.57  Do you ship internationally?
   0.43  Can I change my delivery address?
```
The top result is right every time, and it is always clearly ahead of the second one. Notice that none of the questions share key words with the FAQ they found ("broken" vs "damaged", "Japan" vs "internationally").

## How it works
1. `faq` is a plain Python list of 10 questions: your "documents".
2. `faq_vectors = np.array(embed(faq))` embeds all 10 at once (**step 1**). The result is a table of 10 rows × 384 numbers. This happens once, when the program starts.
3. `questions = sys.argv[1:] or [...]`: `sys.argv` is the list of words you typed after `python`. `sys.argv[1:]` skips the file name. If you typed nothing, the four example questions are used instead.
4. For each question:
   - `q = np.array(embed([question])[0])` turns the question into 384 numbers (**step 2**).
   - `scores = faq_vectors @ q / (...)` computes the cosine similarity between the question and **all 10 FAQs in one line** (**step 3**). `@` is numpy's "multiply and add up" for whole tables, the same `np.dot` from lesson 21, done 10 times at once.
   - `best = scores.argsort()[::-1][:2]` (**step 4**): `argsort()` gives the positions sorted from lowest to highest score, `[::-1]` flips that to highest first, and `[:2]` keeps the top 2.
   - The inner loop prints each score and FAQ.

```
FAQ list ──► embed once ──► 10 × 384 table ─┐
                                            ├─► compare all ──► sort ──► top 2
question ──► embed ──► 384 numbers ─────────┘
```
That is exactly what a vector database does inside. A real one adds saving to disk, labels and fast search over millions of rows (next lesson).

## If something goes wrong
- **`ModuleNotFoundError: No module named 'numpy'`** (or `chromadb`) → switch on your venv and run the `pip install` line again.
- **Your search only used the first word** (e.g. it searched for `can`) → put the whole question in quotes: `python search.py "can you deliver to Japan?"`. Some shells also treat `?` or `!` specially without quotes.
- **The first run is slow** → it is loading (or, the very first time, downloading) the embedding model. Later runs are quick.
- **A search returns a wrong FAQ with a low score (like 0.20)** → nothing in the FAQ matches your question. Search always returns *something*, even a bad match. Exercise 2 fixes this.

## Try this
1. Replace the 10 FAQs with 5–10 questions about your school, job or hobby, and search them with your own words.
2. Only show results with a score above 0.5, and print `No good match` if there are none.
   <details><summary>Solution</summary>

   Replace the inner `for i in best:` loop with:
   ```python
   good = [i for i in best if scores[i] > 0.5]
   if not good:
       print("   No good match")
   for i in good:
       print(f"   {scores[i]:.2f}  {faq[i]}")
   ```
   Notice that "stop charging me every month" (0.46) now says "No good match" even though its top result was right. Picking the cut-off is a trade-off: too high and you hide good answers, too low and you show bad ones. Real products tune it by testing.
   </details>
3. Show the top 3 results instead of 2, and print the **rank** (1, 2, 3) in front of each one.
   <details><summary>Hint</summary>

   Change `[:2]` to `[:3]`, and loop with `for rank, i in enumerate(best, start=1):`, then print `rank` first.
   </details>

## Check yourself
1. Why are the FAQs embedded once at the start, instead of once per question?
2. What does `scores.argsort()[::-1][:2]` give you?
3. Your help centre has 1 million articles. What part of this program would become slow, and what kind of tool solves that?

<details><summary>Answers</summary>

1. Embedding is the slow part. The FAQs don't change between questions, so doing it once and reusing the numbers saves time.
2. The positions of the 2 FAQs with the highest scores, best first.
3. Comparing the question with a million rows on every search (and holding them all in memory). A vector database stores the numbers on disk and uses a clever index to find the closest ones fast, without checking every row.
</details>

## Learn more (optional)
- Video search: [vector search explained](https://www.youtube.com/results?search_query=vector+search+explained+simply)

## Next
→ [23 · Your first vector database (Chroma)](../23-your-first-vector-database-chroma)
