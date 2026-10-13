# 1.2 · Calculator API: query parameters

**What you build:** `/add?a=2&b=3` returns `5`, plus subtract, multiply and divide.
**Like you're 10:** a vending machine. You press buttons (a=2, b=3), it gives you the answer.

## Run it
```bash
cd level-1-apis/02-calculator-api-query-parameters
pip install -r requirements.txt
uvicorn main:app --reload
```
Try: http://127.0.0.1:8000/add?a=2&b=3 → `"result": 5.0`, then `/divide?a=1&b=0` to see a friendly error.

## Run the tests
```bash
pytest -v
```
Tests are robots that check your API so you don't have to click around after every change. **Professional engineers write tests for everything.** Start the habit now.

## Key ideas
- **Query parameters** come after `?` and are joined with `&`: `?a=2&b=3`.
- **Type hints validate input:** `a: float` means FastAPI rejects `?a=hello` with a **422** error automatically.
- **Status codes:** 200 OK · 400 bad request (your rule) · 404 not found · 422 invalid input (FastAPI's rule) · 500 server crashed (your bug).

## Your turn
1. Add `/power?base=2&exp=10`.
2. Add a test for `/multiply`.
3. Make `/sqrt?x=-1` return a 400 error, and write a test for it.

## Watch
- FastAPI query parameters: https://fastapi.tiangolo.com/tutorial/query-params/
- pytest in 10 minutes: https://www.youtube.com/results?search_query=pytest+tutorial+beginners
