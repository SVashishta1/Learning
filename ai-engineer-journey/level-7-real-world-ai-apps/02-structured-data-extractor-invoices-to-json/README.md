# 7.2 · Structured data extractor: invoices → validated JSON

**What you'll build:** a tool that reads messy invoices, receipts and even a scribbled note (or a PDF), and returns **clean JSON that always matches a schema**. Then *your* code double-checks the maths and flags anything suspicious for human review. Results also go to a CSV, and an optional API accepts uploads.
**Like you're 10:** the AI is a fast but sometimes sloppy assistant filling in a form. You give it the exact form (the schema), and a calculator-wielding teacher (your code) checks its sums before anything is filed.
**Time:** ~1.5 h · **Builds on:** [7.1 Chatbot API with memory](../01-chatbot-api-with-memory-in-a-database) · **Needs:** an Anthropic API key (tests run without one)

## Why this matters
Turning documents into database rows is one of the most common paid AI jobs: invoices, receipts, contracts, CVs, medical forms, shipping labels. Before LLMs this needed a custom template per document layout. Now one schema handles an English email, an Italian receipt and a handwritten-style note. The professional part is what you add around the model: a strict schema, rule checks in code, and a "needs human review" flag.

## What you'll learn
- **Schema**: a precise description of the data you want (field names, types, what may be empty), written as a Pydantic class.
- **Structured outputs**: asking Claude to return JSON that is guaranteed to match your schema, and getting a typed Python object back.
- **Validate in code**: re-checking the model's numbers with plain Python, because models can misread digits.
- **Human-in-the-loop**: flagging doubtful results for a person instead of silently trusting them.
- **Documents as input**: sending a PDF to Claude as a `document` block.

## Before you start
```bash
cd level-7-real-world-ai-apps/02-structured-data-extractor-invoices-to-json
pip install -r requirements.txt
```
- `anthropic`: calls Claude. `pydantic`: defines and validates the schema.
- `fastapi`, `uvicorn[standard]`, `python-multipart`: the optional upload API (`python-multipart` lets FastAPI receive files).
- `httpx`, `pytest`: tests.

**API key:** set `ANTHROPIC_API_KEY` as described in the [Level 7 README](../README.md#api-key-needed-from-here-on). Optional: `export CLAUDE_MODEL=claude-haiku-5-5` for the cheapest runs. Tests need no key.

## Run it
1. From the course root: `cd level-7-real-world-ai-apps/02-structured-data-extractor-invoices-to-json`
2. Tests (offline): `pytest -v`
3. Extract the 3 samples (an English email, an Italian receipt, a messy note): `python extractor.py`
4. Your own PDF: `python extractor.py path/to/invoice.pdf`
5. Optional upload API: `uvicorn api:app --reload`, open http://127.0.0.1:8000/docs → **POST /extract → Try it out**, choose a file, **Execute**.

### What you should see
(Shortened. The exact wording of `notes` and descriptions varies a little between runs; the numbers should match.)
```
=== samples/invoice_email.txt ===
{
  "vendor": "BrightPixel Design LLC",
  "invoice_number": "BP-2291",
  "date": "2026-11-03",
  "currency": "USD",
  "line_items": [
    {"description": "Logo redesign", "quantity": 1.0, "unit_price": 850.0, "total": 850.0},
    {"description": "Social media banners", "quantity": 6.0, "unit_price": 45.0, "total": 270.0},
    {"description": "Rush fee (48h)", "quantity": 1.0, "unit_price": 120.0, "total": 120.0}
  ],
  "subtotal": 1240.0,
  "tax": 99.2,
  "total": 1339.2,
  "notes": "Due by 2026-12-03. Pay to BrightPixel Design LLC, account ending 4471."
}
✅ numbers add up

=== samples/messy_note.txt ===
{ "vendor": "Joe's Plumbing", "invoice_number": "J-07", "date": "2026-09-30", ...
  "subtotal": 187.0, "tax": 0.0, "total": 187.0, ... }
✅ numbers add up

=== samples/receipt_scan.txt ===
{ "vendor": "Cafe Luna", "invoice_number": "00451", "date": "2026-10-14", "currency": "EUR", ...
  "subtotal": null, "tax": 0.82, "total": 9.0, "notes": "Paid by card. VAT 10% included in total." }
✅ numbers add up

Wrote extracted.csv. Open it in Excel or Google Sheets.
```
What to look at:
- "3 Nov 2026", "sept 30 2026" and "14/10/2026" all became `YYYY-MM-DD`.
- The Italian `1,80` (comma decimal) became `1.8`, and "TOTALE EURO" became `"currency": "EUR"`.
- The plumber's note had no table at all, yet "2 hrs labour at 55/hr" became a proper line item (2 × 55 = 110).
- `extracted.csv` has one row per document with a `needs_review` column.

## How it works
```
document (.txt / .pdf) ─► document_content() ─► llm.parse(output_format=Invoice) ─► Claude
                                                                                      │ JSON matching the schema
            ⚠️ needs review  ◄── problems ◄── check_math(invoice) ◄── Invoice object ◄─┘
            ✅ numbers add up
```

1. **The schema.** `LineItem` and `Invoice` are Pydantic classes. Types do real work: `float` means a number, `str | None` means "text or nothing". `Field(description=...)` is sent to the model as instructions ("ISO format YYYY-MM-DD", "0 if explicitly none, null if unknown").
2. **`SYSTEM`** sets the rules: copy numbers exactly, never invent values, use null when something is missing.
3. **`document_content(path)`** builds the user message. A PDF is read as bytes, base64-encoded (turned into plain text characters) and sent as a `{"type": "document", ...}` block, so Claude sees the real page layout. A text file is wrapped in `<document>` tags so the model can tell the document apart from your instruction.
4. **`extract(client, path)`** calls `llm.parse(..., output_format=Invoice)`. The SDK turns `Invoice` into a JSON Schema and sends it as the required output format, so Claude's reply can only be JSON of that shape. The SDK then validates it and gives you `response.parsed_output`, a real `Invoice` object: `invoice.total` is a float, no string parsing needed.
5. **`check_math(inv)`** never trusts the model: each line must satisfy `quantity × unit_price = total` (within 1 cent), the lines must add up to the subtotal, and subtotal + tax must equal the total. Many European receipts quote tax as already *included* ("di cui IVA" = "of which VAT"), so "subtotal equals total" is accepted too. Any failure becomes a readable problem message.
6. **`__main__`** runs on the given files (or every `samples/*.txt`), prints each result with ✅ or ⚠️, and writes `extracted.csv` with `csv.DictWriter`.
7. **`api.py`** receives an upload, saves it to a temporary file (keeping the `.pdf`/`.txt` suffix so `extract()` knows the type), extracts, deletes the temporary file, and returns `{"invoice", "needs_review", "problems"}`. The client is created on the first request, so the app starts (and tests run) without a key.
8. **`test_extractor.py`** checks `check_math` on a correct and a wrong invoice, checks that `extract()` really sends the `Invoice` schema (via `FakeClient`), and calls the API with a bad invoice to confirm it's flagged.

## If something goes wrong
- **`anthropic.AuthenticationError` / "Could not resolve authentication method"** → set `ANTHROPIC_API_KEY` in this terminal (see the Level 7 README).
- **`No documents found`** → you ran `python extractor.py` from another folder. `cd` into this project folder first, or pass full paths.
- **`Form data requires "python-multipart" to be installed`** when starting the API → run `pip install -r requirements.txt` again.
- **`⚠️ needs human review` on your own invoice** → that's the feature working. Read the problem message: often the document itself has a rounding or discount line, or the model misread a digit. Check the original by hand.
- **A big PDF fails with a request-size error** → PDFs must be under 32 MB and 600 pages. Split large files or send only the relevant pages.

## Try this
1. **Add a category.** Give `Invoice` a field `category: Literal["food", "software", "services", "travel", "other"]` and see what each sample gets.
   <details><summary>Solution</summary>

   ```python
   from typing import Literal

   class Invoice(BaseModel):
       ...
       category: Literal["food", "software", "services", "travel", "other"] = Field(
           description="What kind of spending this is")
   ```
   `Literal` restricts the value to exactly those strings, and structured outputs enforce it, so you'll never get "Food & drink" or "misc". Add the column to `rows` in `__main__` to see it in the CSV. Also update `make()` in `test_extractor.py` (add `category="other"`) or the tests will fail: a good example of how a schema change ripples through code.
   </details>
2. **One more business rule.** Flag any invoice whose `date` is in the future or whose `currency` isn't 3 capital letters.
   <details><summary>Solution</summary>

   Add to `check_math` before `return problems`:
   ```python
   from datetime import date
   if inv.date and inv.date > date.today().isoformat():      # ISO dates compare correctly as text
       problems.append(f"date {inv.date} is in the future")
   if not (len(inv.currency) == 3 and inv.currency.isupper()):
       problems.append(f"currency '{inv.currency}' isn't an ISO code")
   ```
   Then add a test that builds an invoice dated `"2999-01-01"` and asserts the problem appears.
   </details>
3. **A CV parser.** Make `cv_parser.py` with a `Candidate` schema (name, email, skills, years of experience, education) and run it on your own CV saved as a PDF.
   <details><summary>Hint</summary>

   Copy `extractor.py`. Replace `LineItem`/`Invoice` with `class Education(BaseModel): school: str; degree: str | None; year: int | None` and `class Candidate(BaseModel): name: str; email: str | None; skills: list[str]; years_experience: float | None; education: list[Education]`. Change `SYSTEM` and the prompt text, pass `output_format=Candidate`, and replace `check_math` with checks that make sense for CVs (for example, `years_experience` between 0 and 60).
   </details>

## Check yourself
1. Structured outputs guarantee valid JSON of the right shape. Why do you still need `check_math`?
2. Why is `tax` declared as `float | None` instead of just `float`?
3. What does `Field(description=...)` do here besides documenting the code?
4. Your company processes 10,000 invoices a month. How would `needs_review` change the workflow?

<details><summary>Answers</summary>

1. The shape can be perfect while a value is wrong: a misread 7 as 1, a swapped quantity and price. The schema checks types; only your rules check that the numbers make sense.
2. So the model can honestly say "not stated" (`null`) instead of being forced to invent a number. Inventing values is worse than admitting a gap.
3. It's included in the schema sent to Claude, so it acts as per-field instructions (formats, what null means).
4. Invoices with no problems can flow straight into accounting; only the flagged ones go to a person. That's how AI saves time without losing control.
</details>

## Learn more (optional)
- Structured outputs: https://platform.claude.com/docs/en/build-with-claude/structured-outputs
- PDF support: https://platform.claude.com/docs/en/build-with-claude/pdf-support
- Pydantic models, the basics: https://docs.pydantic.dev/latest/concepts/models/

## Next
→ [7.3 · RAG: ask questions about your PDFs](../03-rag-ask-questions-about-your-pdfs)
