# Practice coding problems (FDE-style)

FDE coding interviews are rarely about clever algorithms. They are about **messy real data**, **unreliable systems** and **clear code under time pressure**. Give yourself 30 minutes per problem, talk out loud, write tests. Solutions are in `solutions.py`, tests in `test_solutions.py`.

## 1. Merge customer contacts (30 min)
A customer exports contacts from two systems. Write `merge_contacts(rows: list[dict]) -> list[dict]`:
- Each row has `name`, `email`, `phone` (any may be missing or empty).
- Normalise: email lowercased and stripped; phone digits only, with a leading `+` kept (`"+31 (0)6 1234-5678"` → `"+31612345678"`: drop the `(0)` trunk prefix); name stripped with single spaces.
- Two rows are the same person if they share a normalised email OR a normalised phone.
- Merge each group into one row: the longest name, the first non-empty email and phone, and `sources`: how many rows were merged.
- Keep the order of first appearance.

Follow-ups an interviewer may ask: `0612345678` and `+31612345678` are the same Dutch number; how would you catch that? (convert to the international E.164 format with the `phonenumbers` library and the customer's default country). What if A matches B by email and B matches C by phone? (transitive: union-find). How would you scale to 10 million rows? (block on normalised keys, run in a database or Spark). What would you ask the customer? (which system is the source of truth for each field).

## 2. Fetch every page from a flaky API (30 min)
Write `fetch_all(get_page, max_retries=3, sleep=time.sleep) -> list`:
- `get_page(cursor)` returns `{"items": [...], "next": "<cursor or None>"}`; start with `cursor=None`.
- It sometimes raises `TemporaryError` (think HTTP 503/429). Retry that page with exponential backoff (1, 2, 4 s ...), at most `max_retries` retries per page, then re-raise.
- Any other exception is raised immediately (don't retry a 401).
- Return all items in order. Detect a loop: if the API returns a cursor you have already seen, stop with `ValueError`.

Follow-ups: how do you make it resumable after a crash? (persist the last cursor); idempotency for writes (`Idempotency-Key`); rate limits (respect `Retry-After`).

## 3. Chunk a document for RAG (20 min)
Write `chunk(text, max_words=120, overlap=20) -> list[str]`: split on blank lines into paragraphs, pack paragraphs into chunks of at most `max_words` words, split a paragraph longer than `max_words` by words, and start each chunk (after the first) with the last `overlap` words of the previous chunk.

Follow-ups: why overlap? (an answer split across a boundary stays findable); why chunk by structure first? (headings and paragraphs keep meaning together); how do you evaluate chunk size? (a golden question set and recall@k, lesson 11).
