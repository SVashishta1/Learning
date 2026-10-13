# 7.2 · Structured data extractor: invoices → validated JSON

**What you build:** a tool that reads messy invoices, receipts and even a scribbled note (or a PDF), and returns **clean JSON that always matches a schema**. Then *your* code double-checks the maths and flags anything suspicious for human review. Results also go to a CSV.
**Like you're 10:** the AI is a fast but sometimes sloppy assistant filling in a form. You give it the exact form (the schema), and a calculator-wielding teacher (your code) checks its sums before anything is filed.

This is one of the **most common paid AI jobs**: extracting data from documents (invoices, contracts, CVs, medical forms) into databases.

## Run it
```bash
cd level-7-real-world-ai-apps/02-structured-data-extractor-invoices-to-json
pip install -r requirements.txt
export ANTHROPIC_API_KEY=sk-ant-...
python extractor.py                       # runs on the 3 samples (English email, Italian receipt, messy note)
python extractor.py path/to/invoice.pdf   # your own PDF
uvicorn api:app --reload                  # optional upload API at /docs
```
Tests (offline): `pytest -v`

## Key ideas
- **Pydantic schema → structured outputs:** `llm.parse(..., output_format=Invoice)` constrains the model to return JSON matching your schema. You get a typed Python object back, no fragile string parsing.
- **`Field(description=...)`** doubles as instructions to the model ("ISO format", "null if unknown").
- **Never trust, always verify:** `check_math()` re-adds the numbers. LLMs can misread digits, so production systems combine AI extraction with rule-based validation and a **human-in-the-loop** for flagged cases.
- **Multilingual and multi-format for free:** the Italian receipt with comma decimals and the informal plumber note both come out in the same shape.
- **PDF input:** sent as a `document` block, so Claude reads the layout and text directly.

## Your turn
1. Add a `category` field with `Literal["food", "software", "services", "travel", "other"]`.
2. Extract from 20 real receipts (photos work too: send `{"type": "image", ...}` blocks) and measure accuracy against your own hand-labelled answers. That's an eval (→ 7.5).
3. Build a "CV parser" with a `Candidate` schema (name, skills, years of experience, education).

## Read
- Structured outputs: https://platform.claude.com/docs/en/build-with-claude/structured-outputs
- PDF support: https://platform.claude.com/docs/en/build-with-claude/pdf-support
