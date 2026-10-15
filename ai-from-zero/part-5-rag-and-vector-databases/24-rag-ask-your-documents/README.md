# 24 · RAG: ask your documents

**What you'll build:** a program that reads every PDF, text and Markdown file in the `docs/` folder, stores them in a vector database, and answers your questions **using only your documents**, with sources like `[1]`. It comes with a sample company handbook (holidays, expenses, IT rules), and you can drop in your own PDFs.
**Time:** ~1 hour · **Builds on:** [23 · Your first vector database](../23-your-first-vector-database-chroma) and the `ai.py` helper from [Part 4](../../part-4-chatbots) · **Needs:** an Anthropic API key

## Why this matters
An AI on its own doesn't know your company's handbook, your lecture notes or last week's contract, and when it doesn't know, it may invent an answer. **RAG** fixes both problems: find the right passages first, then let the AI answer from them and cite them. Company "ask HR" bots, customer-support assistants and "chat with your PDF" tools are built exactly like this, and it is one of the most common jobs for AI engineers today.

## What you'll learn
- **RAG (Retrieval-Augmented Generation):** *retrieve* relevant passages, then let the AI *generate* an answer from them.
- **Chunking:** cutting long documents into short pieces (~500 characters), so search can return just the part that matters.
- **Grounding:** telling the AI to answer *only* from the sources you give it, so it doesn't make things up.
- **Citations:** numbering the sources (`[1]`, `[2]`) so you can check where every fact came from.

## Before you start
- Install the Part 5 packages (once):
  ```bash
  pip install chromadb numpy pypdf anthropic fastapi "uvicorn[standard]" python-multipart
  ```
  Used here: `chromadb` (vector database), `pypdf` (reads text out of PDFs), `anthropic` (talks to Claude).
- Set your API key in the terminal you'll use (full steps, including how to get a key, are in the [Part 4 README](../../part-4-chatbots)):
  ```bash
  export ANTHROPIC_API_KEY=sk-ant-your-key-here        # Mac
  $env:ANTHROPIC_API_KEY="sk-ant-your-key-here"        # Windows PowerShell
  ```
  Optional, cheaper while learning: `export CLAUDE_MODEL=claude-haiku-5-5` (Mac) or `$env:CLAUDE_MODEL="claude-haiku-5-5"` (Windows).

## Run it
1. From the course folder (`Learning/ai-from-zero`), with your venv switched on:
   ```bash
   cd part-5-rag-and-vector-databases/24-rag-ask-your-documents
   python ask.py "How many vacation days can I carry over, and until when?"
   ```
2. Ask as many questions as you like (press Enter on an empty line to stop):
   ```bash
   python ask.py
   ```
3. Ask something that is **not** in the documents, like `What's the CEO's salary?`. It should say it couldn't find it instead of inventing an answer.
4. Drop **your own PDFs** (lecture notes, a manual, a contract) or `.txt`/`.md` files into `docs/` and ask about them.

### What you should see
```
📄 expense_policy.md: 2 chunks
📄 it_security.md: 3 chunks
📄 vacation_policy.md: 3 chunks

✅ 8 chunks stored in the vector database.


💬 You can carry over up to 5 unused days into the next year [1]. They must be used before March 31, otherwise they expire [1].

   [1] vacation_policy.md: # Acme Robotics: Vacation and Leave Policy  ## Annual leave Full-time employees ...
   [2] vacation_policy.md: ## Requesting leave Requests must be submitted in the HR portal at least 2 weeks...
   [3] vacation_policy.md: ## Parental leave Primary caregivers receive 20 weeks of fully paid parental lea...
   [4] expense_policy.md: # Acme Robotics: Travel and Expense Policy  ## Meals While travelling, meals are...
```
Claude's wording will differ each time; the chunk counts and the list of sources are exactly what the program prints. Check the answer against source `[1]`: the carry-over rule really is in that chunk. Sources `[2]`–`[4]` were also sent to Claude, but it only used `[1]`.

For `What's the CEO's salary?` you should get something like `💬 I couldn't find that in your documents.`

## How it works
All the RAG work happens in `rag.py`, in five steps. `ask.py` is just the part you talk to.

```
docs/ ─► READ ─► CUT into chunks ─► STORE in Chroma          (once, when the program starts)

question ─► FIND 4 closest chunks ─► ASK Claude: "answer ONLY from these, cite [1]..." ─► answer + sources
```

1. **Read.** `read_file(path)` returns the text of one file. For a PDF, `PdfReader(path).pages` gives each page and `extract_text()` pulls out its words. Other files are read as plain text.
2. **Cut.** `cut_into_chunks(text, size=500)` first splits the text at blank lines (paragraphs). A paragraph that is still longer than `size` is cut at the last space before the limit (PDFs often have no blank lines at all). Then small pieces are glued together until a chunk is about 500 characters. Why chunks? Search works best on short, focused pieces, and sending Claude 4 short chunks is cheaper and clearer than whole documents.
3. **Store.** `add_document(path)` removes that file's old chunks (`library.delete(where={"source": ...})`, in case the file changed), then `upsert`s the new ones with ids like `vacation_policy.md-0` and a `source` label. Chroma makes the embeddings. `add_folder("docs")` does this for every `.txt`, `.md` and `.pdf` file.
4. **Find.** `find_relevant(question, how_many=4)` asks Chroma for the 4 chunks closest in meaning to your question, exactly like lesson 23.
5. **Ask.** `answer(question)` numbers the chunks (`[1] (from vacation_policy.md) ...`), wraps them in `<sources>` tags, adds your question, and sends it to Claude with the `RULES` as its system prompt: use only the sources, cite them, and say "I couldn't find that" otherwise. It returns Claude's reply **and** the sources, so `ask.py` can print both.

In `ask.py`, `ask_and_show(question)` calls `rag.answer` and prints the reply and a one-line preview of each source. If you typed a question after `python ask.py`, it answers that one; otherwise the `while True:` loop keeps asking until you press Enter on an empty line.

## If something goes wrong
- **`❌ ANTHROPIC_API_KEY is not set`** or **`❌ Your API key is wrong`** → set the key in *this* terminal (see Before you start). Every new terminal window needs it again.
- **A PDF says `0 chunks`** → it is a scanned PDF (pictures of pages, no real text inside). Try selecting text in it with your mouse: if you can't, `pypdf` can't read it either. Use a PDF with real text, or copy the text into a `.txt` file.
- **Answers mention a file you already deleted from `docs/`** → its chunks are still in the database. Delete the `chroma_data` folder and run again; it is rebuilt from `docs/` in seconds.
- **`anthropic.RateLimitError` or `overloaded_error`** → you sent too many requests too fast, or Claude is busy. Wait a minute and try again.
- **It says "I couldn't find that" but the answer IS in your document** → the right chunk wasn't in the top 4. Try asking with words closer to the document's wording, or do exercise 2 below.

## Try this
1. Ask: `Do I need a doctor's note if I'm sick for 2 days?`. Is the answer right? Which source did it use?
   <details><summary>Hint</summary>

   The sick-leave rule says a note is needed for absences **longer than 3 consecutive days**, so the answer should be "no", citing the vacation policy. This is a good test: the AI has to *reason* with the rule, not just copy it.
   </details>
2. Change `how_many: int = 4` to `1` in `find_relevant`, then ask `How many vacation days do I get, and how long must my password be?`. Then try `8`. What changes?
   <details><summary>Hint</summary>

   The answer lives in two different files. With 1 chunk, Claude only sees the IT security chunk, so it can answer the password half (14 characters) but says it couldn't find the vacation half. With 8 it sees almost everything: answers get more complete, but each question costs more and irrelevant chunks can sneak in. Picking "how many" is a real trade-off.
   </details>
3. Remove the line `If the sources don't contain the answer, say "I couldn't find that in your documents."` from `RULES`, and ask `What's the CEO's salary?` again. What does the AI do now? Put the line back afterwards.
   <details><summary>Hint</summary>

   It may still refuse (modern models are fairly careful), or it may guess or explain that salaries aren't in the handbook in a long-winded way. The point: clear rules in the system prompt make the behaviour **predictable**, which is what a real product needs.
   </details>

## Check yourself
1. What are the 5 steps of RAG, in order?
2. Why are documents cut into chunks instead of being stored whole?
3. Why does the prompt number the sources and ask for `[1]`-style citations?
4. You add a new PDF to `docs/`. Why do you have to run the program again before you can ask about it?

<details><summary>Answers</summary>

1. Read the files, cut them into chunks, store the chunks (with embeddings) in a vector database, find the chunks closest to the question, ask the AI to answer from those chunks.
2. Search finds the specific passage that matters, and the AI gets a few short, relevant pieces instead of whole documents (cheaper, clearer, and it fits in the request).
3. So you (or your users) can check where each fact came from, and spot when the AI says something no source supports.
4. Files are only read and stored when the program starts (`rag.add_folder("docs")`). Until then, the new PDF isn't in the vector database, so search can't find it.
</details>

## Learn more (optional)
- Video search: [RAG explained](https://www.youtube.com/results?search_query=retrieval+augmented+generation+explained)
- [Claude docs: citations](https://platform.claude.com/docs/en/build-with-claude/citations) (a built-in way to get cited answers, for later)

## Next
→ [25 · RAG chat web app](../25-rag-chat-web-app)
