# 1.2 · Calculator API: query parameters + first tests

**What you'll build:** a calculator API where `/add?a=2&b=3` answers `5.0` (plus subtract, multiply and divide), friendly errors for bad input, and your first automated tests.
**Like you're 10:** a vending machine. You press buttons (a=2, b=3) and it gives you the answer. If you press nonsense, a little screen says why instead of the machine breaking.
**Time:** ~45 min · **Builds on:** [1.1 · Hello API](../01-hello-api-the-waiter-says-hi) · **Needs:** nothing extra

## Why this matters
Real APIs take inputs (a search term, a page number, a model temperature) and must reject bad ones politely. And professional teams never "click around" to check their API after each change: they run **tests** that do it in a second. Every later project in this course comes with tests, and so does every serious AI codebase.

## What you'll learn
- **Query parameters:** inputs after the `?` in a URL, joined with `&`: `?a=2&b=3`.
- **Validation with type hints:** `a: float` makes FastAPI reject `?a=hello` with a 422 error, for free.
- **Status codes:** 200 OK, 400 bad request (your rule), 404 not found, 422 invalid input (FastAPI's rule), 500 server crashed (your bug).
- **HTTPException:** how your code says "no" with the right status code and message.
- **Tests with pytest:** small functions that call your API and `assert` the answer is right.

## Before you start
```bash
cd level-1-apis/02-calculator-api-query-parameters
pip install -r requirements.txt
```
- `fastapi`, `uvicorn[standard]`: the web framework and server (as in 1.1).
- `pytest`: finds and runs your tests.
- `httpx`, `httpx2`: HTTP clients that FastAPI's `TestClient` uses behind the scenes (newer FastAPI versions use `httpx2`).

No API key needed.

## Run it
1. Start the server:
   ```bash
   uvicorn main:app --reload
   ```
2. Try these in the browser:
   - http://127.0.0.1:8000/add?a=2&b=3
   - http://127.0.0.1:8000/divide?a=1&b=0
   - http://127.0.0.1:8000/add?a=hello&b=3
   - http://127.0.0.1:8000/multiply?a=1e308&b=10
3. Stop the server (`Ctrl+C`) and run the tests:
   ```bash
   pytest -v
   ```

### What you should see
In the browser:
```
/add?a=2&b=3            {"operation":"add","a":2.0,"b":3.0,"result":5.0}
/divide?a=1&b=0         {"detail":"Cannot divide by zero"}                                   (status 400)
/add?a=hello&b=3        {"detail":[{"type":"float_parsing","loc":["query","a"],
                         "msg":"Input should be a valid number, unable to parse string as a number","input":"hello"}]}   (status 422)
/add?a=2                {"detail":[{"type":"missing","loc":["query","b"],"msg":"Field required","input":null}]}       (status 422)
/multiply?a=1e308&b=10  {"detail":"Result is not a finite number"}                           (status 400)
```
From `pytest -v`:
```
test_main.py::test_add PASSED                                            [ 20%]
test_main.py::test_divide_by_zero_is_a_400 PASSED                        [ 40%]
test_main.py::test_missing_parameter_is_a_422 PASSED                     [ 60%]
test_main.py::test_wrong_type_is_a_422 PASSED                            [ 80%]
test_main.py::test_too_big_result_is_a_400 PASSED                        [100%]

============================== 5 passed in 0.74s ===============================
```
Notice the two kinds of error: **422** comes from FastAPI (the input had the wrong shape), **400** comes from *your* code (the input was valid, but your rules say no). `"loc":["query","a"]` tells the caller exactly which input was wrong.

## How it works
```
GET /divide?a=1&b=0 ──► FastAPI reads a, b from the URL ──► float? no → 422
                                                        └─► yes → divide(a=1.0, b=0.0) ──► b == 0 → HTTPException(400)
```
1. **Query parameters:** `def add(a: float, b: float)` has arguments that are *not* in the path (`/add`), so FastAPI looks for them after the `?`. It converts the text `"2"` to the float `2.0` because of the type hint. Missing or non-numeric → 422 before your function runs.
2. **`answer(operation, a, b, result)`** builds the reply dict for every route, so the four routes stay one line each. It also checks `math.isfinite(result)`: numbers too big for a float become "infinity", and JSON has no way to write that, so we return a clear 400 instead of crashing with a 500.
3. **`divide()`** checks `if b == 0` first and does `raise HTTPException(status_code=400, detail="Cannot divide by zero")`. `raise` stops the function and FastAPI turns the exception into a JSON error response.
4. **`test_main.py`**: `client = TestClient(app)` is a pretend browser that calls your app directly in memory, no server needed. Each `test_...` function makes a request and uses `assert` to check the status code and the JSON. pytest runs every function whose name starts with `test_`; if an `assert` is false, that test FAILS and shows you what went wrong.

## If something goes wrong
- **`ModuleNotFoundError: No module named 'httpx'`** (or `'httpx2'`) when running pytest → you skipped the install. Run `pip install -r requirements.txt` with your venv active.
- **`ModuleNotFoundError: No module named 'main'`** in pytest → run `pytest` from inside `02-calculator-api-query-parameters`, where `main.py` is.
- **pytest says `no tests ran`** → test files must be named `test_*.py` and test functions must start with `test_`.
- **`/add?a=2 b=3` gives 422** → query parameters are joined with `&`, not spaces: `?a=2&b=3`.
- **Port already in use** → stop the old server with `Ctrl+C`, or add `--port 8001`.

## Try this
1. Add `/power?base=2&exp=10` (answer: `1024.0`).
   <details><summary>Solution</summary>

   ```python
   @app.get("/power")
   def power(base: float, exp: float):
       return answer("power", base, exp, base ** exp)
   ```
   Careful: `(-8) ** 0.5` gives a *complex* number in Python, so `/power?base=-8&exp=0.5` crashes with a **500**. Can you reject it with a 400? (Hint: `isinstance(result, complex)`.)
   </details>
2. Write a test for `/multiply`.
   <details><summary>Solution</summary>

   ```python
   def test_multiply():
       r = client.get("/multiply", params={"a": 4, "b": 2.5})
       assert r.status_code == 200
       assert r.json()["result"] == 10
   ```
   `params={...}` builds `?a=4&b=2.5` for you.
   </details>
3. Add `/sqrt?x=9` (answer `3.0`) that returns a **400** for negative numbers, and write a test for both cases.
   <details><summary>Solution</summary>

   ```python
   @app.get("/sqrt")
   def sqrt(x: float):
       if x < 0:
           raise HTTPException(status_code=400, detail="Cannot take the square root of a negative number")
       return {"operation": "sqrt", "x": x, "result": math.sqrt(x)}
   ```
   ```python
   def test_sqrt():
       assert client.get("/sqrt?x=9").json()["result"] == 3
       assert client.get("/sqrt?x=-1").status_code == 400
   ```
   </details>

## Check yourself
1. In `/add?a=2&b=3`, which part is the path and which part is the query string?
2. Why does `/add?a=hello&b=3` give 422 even though `add()` has no `if` checks?
3. When should *your* code raise a 400 instead of letting FastAPI's 422 handle it?
4. Why can tests use `TestClient` without starting uvicorn?

<details><summary>Answers</summary>

1. The path is `/add`; the query string is `a=2&b=3` (everything after `?`).
2. The type hint `a: float` tells FastAPI to convert and check the input before calling `add()`. "hello" isn't a number, so FastAPI rejects it.
3. When the input has the right type but breaks a rule only your code knows, like dividing by zero.
4. `TestClient` calls the FastAPI `app` object directly in memory, the same way a server would, so no network or server process is needed.
</details>

## Learn more (optional)
- FastAPI query parameters: https://fastapi.tiangolo.com/tutorial/query-params/
- FastAPI testing: https://fastapi.tiangolo.com/tutorial/testing/
- pytest in 10 minutes: https://www.youtube.com/results?search_query=pytest+tutorial+beginners

## Next
→ [1.3 · Joke & quote API: random picks + POST](../03-joke-and-quote-api-random-picks)
