# 20 · AI turns messy text into data

**What you'll build:** a program that reads 3 messy receipts (one in Italian, one an informal note, one an email), fills in the **same tidy form** for each, and saves them as a spreadsheet (`receipts.csv`).
**Time:** ~45 min · **Builds on:** [16 · Your first message to an AI](../16-your-first-message-to-an-ai) and [17 · Chatbot with memory](../17-chatbot-with-memory) (the `ai.py` helper) · **Needs:** an Anthropic API key (see the [Part 4 README](../README.md))

## Why this matters
Businesses are full of messy text: invoices, emails, support tickets, CVs, contracts. Turning it into clean rows and columns used to need a person typing, or fragile code that broke on every new layout. **Structured output** (the AI fills in a form you define, and must stick to it) is one of the most common paid uses of AI in companies, because the result can go straight into a spreadsheet, database or another program.

## What you'll learn
- **A form as a Pydantic class:** `class Receipt(BaseModel)` lists the boxes you want filled in and what type each one is.
- **Structured output:** Claude is forced to answer in exactly that shape, so your code gets data, not a chatty paragraph.
- **Validation:** the answer is checked and turned into a real Python object (`receipt.total` is a number you can add up).
- **CSV files:** a simple table format that Excel and Google Sheets open.

## Before you start
- Install (with your virtual environment on):
  ```bash
  pip install anthropic pydantic
  ```
  `anthropic` talks to Claude; `pydantic` describes the form. Or the whole Part 4 line: `pip install anthropic fastapi "uvicorn[standard]" pydantic`
- **API key:** `ANTHROPIC_API_KEY` must be set in your terminal (see **Get your API key** in the [Part 4 README](../README.md)).
- Files here: `extract.py` (the project) and `ai.py` (the helper from project 17).

## Run it
1. Open a terminal in the `ai-from-zero` folder.
2. Run:
   ```bash
   cd part-4-chatbots/20-ai-turns-messy-text-into-data
   python extract.py
   ```
3. Open the new `receipts.csv` in Excel, Numbers or Google Sheets (File → Import).

### What you should see
One line per receipt, then a message about the file. The exact text Claude picks can vary a little:
```
✅ CAFE LUNA            14/10/2026       5.10 EUR  items: ['2x cappuccino', 'cornetto']
✅ Joe's Plumbing       sept 30        142.00 USD  items: ['kitchen tap repair', 'new hose']
✅ Amazon               Oct 2, 2026     34.49 USD  items: ['USB-C cable', 'Desk lamp']

Saved receipts.csv. Open it in Excel or Google Sheets!
```
Look at how different the three inputs were, yet each came out with the same 5 boxes. Claude turned "TOTALE EUR 5,10" into the number `5.10` and `"EUR"`, and worked out `"USD"` from a `$` sign. `receipts.csv` looks like this:
```
shop,date,total,currency,items
CAFE LUNA,14/10/2026,5.1,EUR,"2x cappuccino, cornetto"
Joe's Plumbing,sept 30,142.0,USD,"kitchen tap repair, new hose"
Amazon,"Oct 2, 2026",34.49,USD,"USB-C cable, Desk lamp"
```
Notice the dates are written three different ways, because the system prompt says "exactly as written". Try this #2 fixes that.

## How it works
```
messy text ──→ ai.ask_for_data(text, Receipt) ──→ Claude (must answer in the Receipt shape)
                                                        │
Receipt object ←── checked and converted by Pydantic ←──┘ {"shop": ..., "total": 5.1, ...}
      │
      └──→ printed line + one row in receipts.csv
```
1. **The form.** `class Receipt(BaseModel)` has five boxes: `shop` (text), `date` (text, or `None` if the text has no date: that's what `str | None` means), `total` (a decimal number), `currency` (text) and `items` (a list of texts).
2. **The inputs.** `messy_texts` is a list of three very different strings.
3. **Filling in the form.** For each text, `ai.ask_for_data(prompt, Receipt)` is called. Inside `ai.py` it uses `client().beta.messages.parse(..., output_format=Receipt)`. The Anthropic library turns your class into a description of the form (a JSON schema), sends it with the request, and Claude's answer is **constrained** to match it: right box names, right types, nothing extra. The library then checks the answer and gives you a real `Receipt` object (`response.parsed_output`).
4. **Using the data.** Because it's an object, not text, you can write `receipt.total` and format it as a number (`:8.2f` means "8 characters wide, 2 decimals"). `receipt.date or '?'` shows `?` if the date was missing.
5. **Saving a spreadsheet.** `receipt.model_dump()` turns the object into a dictionary; the list of items is joined into one text cell. `csv.DictWriter` writes a header row and one row per receipt. The columns come from `Receipt.model_fields`, so if you add a box to the form, it becomes a new column automatically. `encoding="utf-8-sig"` makes Excel show € signs and accents correctly.

## If something goes wrong
- **`❌ ANTHROPIC_API_KEY is not set in this terminal`** → set it in this terminal (Part 4 README, Step 4) and run again.
- **`PermissionError: [Errno 13] Permission denied: 'receipts.csv'`** → the file is open in Excel. Close it and run again.
- **`ValidationError`** or **`AttributeError: 'NoneType' object has no attribute 'shop'`** → Claude's answer couldn't be read as the form (very rare; for example the reply was cut off). Run it again; if it keeps happening, make the text shorter.
- **`TypeError: unsupported operand type(s) for |`** → your Python is older than 3.10, which doesn't understand `str | None`. Install a newer Python (see [00 · Start here](../../00-start-here)); the `anthropic` library needs 3.10+ anyway.
- **A box always comes back empty (`{}`)** → you used a plain `dict` type. Structured output needs every box spelled out: use `str`, `int`, `float`, `bool`, `list[...]`, `... | None` or another `BaseModel` class.
- **Weird characters in Excel** (like `â‚¬`) → you opened an old file made without `utf-8-sig`. Run the program again, or use Excel's Data → From Text/CSV and choose UTF-8.

## Try this
1. **Add a box.** Add `category: str` (food, home, services...) to `Receipt` and run it again.
   <details><summary>Hint</summary>

   Add the line `    category: str` under `items: list[str]`. Claude picks a sensible category for each receipt (for example "food", "home repair", "electronics") and a `category` column appears in the CSV by itself. Want Claude to choose only from fixed options? Use `category: Literal["food", "home", "services", "shopping"]` with `from typing import Literal` at the top.
   </details>
2. **Make every date look the same.** Change the `date` box so Claude always writes dates as `YYYY-MM-DD`.
   <details><summary>Solution</summary>

   Change the import to `from pydantic import BaseModel, Field` and the box to:
   ```python
       date: str | None = Field(description="The date as YYYY-MM-DD. Use null if there is no date.")
   ```
   The description travels with the form, so Claude reads it. Now you get `2026-10-14`, `2026-09-30` (Claude guesses the year from context, or leaves it null) and `2026-10-02`. Descriptions are how you give per-box instructions.
   </details>
3. **A new form.** Make a `JobPost` form (title, company, salary, skills) and feed it two job adverts you find online or write yourself.
   <details><summary>Solution</summary>

   Make a new file `jobs.py` in this folder:
   ```python
   from pydantic import BaseModel

   import ai


   class JobPost(BaseModel):
       title: str
       company: str
       salary: str | None          # None if the advert doesn't say
       skills: list[str]


   adverts = [
       "We're hiring! Junior Python Developer at Bright Apps Ltd, London. £32k-£38k. You know Python, SQL and Git; Docker is a plus.",
       "Acme Robotics seeks a Data Analyst (remote). Must love Excel, SQL and dashboards. Salary depends on experience.",
   ]

   for advert in adverts:
       job = ai.ask_for_data(f"Fill in the job form from this advert:\n{advert}", JobPost)
       print(f"{job.title} at {job.company} | salary: {job.salary or '?'} | skills: {', '.join(job.skills)}")
   ```
   Run `python jobs.py`. Same three steps every time: describe the form, call `ask_for_data`, use the object.
   </details>

## Check yourself
1. Why is a filled-in `Receipt` object more useful to your code than a paragraph of text?
2. What does `date: str | None` allow that `date: str` doesn't?
3. Who makes sure Claude's answer has exactly the right boxes and types?
4. Name two real business jobs this technique could do.

<details><summary>Answers</summary>

1. Your code can use each box directly (`receipt.total + 10`, sort by `shop`, save to a database) without trying to find the numbers inside sentences.
2. The box may be empty (`None`) when the text doesn't contain a date, instead of forcing Claude to make one up.
3. Both sides: the API constrains Claude's answer to the form you sent, and Pydantic checks it again and converts it into a Python object.
4. For example: reading invoices into accounting software, pulling names and dates from contracts, sorting support emails by topic and urgency, turning CVs into a candidate table.
</details>

## Learn more (optional)
- Structured outputs (official docs): https://platform.claude.com/docs/en/build-with-claude/structured-outputs
- Pydantic models, the "forms" used here: https://docs.pydantic.dev/latest/concepts/models/

## Next
→ [21 · What is an embedding?](../../part-5-rag-and-vector-databases/21-what-is-an-embedding) (Part 5 · RAG & vector databases)
