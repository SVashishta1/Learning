# 01 · Your first API

**What you'll build:** a tiny web service that turns 3 small Python functions into web addresses your browser can visit, plus a free "control panel" page to test them.
**Time:** ~30 min · **Builds on:** [00 · Start here](../../00-start-here) · **Needs:** nothing extra

Like you're 10: an API is a waiter. You (the browser) ask for something from the menu, the waiter (your code) fetches it and brings it back on a plate (JSON).

## Why this matters
Every AI product you've used sits behind an API: the ChatGPT and Claude apps send your message to an API and show the answer. When AI engineers "ship a model", they usually wrap it in an API exactly like this one so websites and phone apps can use it. FastAPI, the tool you use here, is one of the most popular ways to do that in Python.

## What you'll learn
- **API**: a set of web addresses ("endpoints") that programs can call to get data back.
- **Endpoint**: one address, like `/hello/Sam`, connected to one Python function.
- **JSON**: the text format APIs answer in. It looks like a Python dictionary: `{"message": "Hi"}`.
- **Path and query parameters**: the two ways to send inputs in an address: `/hello/Sam` (inside the path) and `/add?a=2&b=3` (after the `?`).
- **Server**: a program that keeps running and waits for visitors. `uvicorn` is the server that runs your FastAPI code.

## Before you start
- Switch on your venv (see [00 · Start here](../../00-start-here), step 6), then install this part's add-ons once:
  ```bash
  pip install fastapi "uvicorn[standard]" httpx
  ```
  - `fastapi`: turns Python functions into web addresses and checks inputs for you.
  - `uvicorn[standard]`: the server that runs your API and listens for visitors.
  - `httpx`: lets your own code call other APIs (used in lesson 04).
- No API key needed.

## Run it
1. From the course folder (`ai-from-zero`), go into this lesson's folder:
   ```bash
   cd part-1-apis/01-your-first-api
   ```
2. Start the server:
   ```bash
   uvicorn main:app --reload
   ```
   `main:app` means "the variable `app` inside the file `main.py`". `--reload` restarts the server every time you save the file.
3. **Leave that terminal running.** Open these addresses in your web browser:
   - http://127.0.0.1:8000/
   - http://127.0.0.1:8000/hello/Sam
   - http://127.0.0.1:8000/add?a=2&b=3
   - http://127.0.0.1:8000/docs (the free control panel)
4. When you're done, click in the terminal and press **Ctrl + C** to stop the server.

### What you should see
In the terminal:
```
INFO:     Will watch for changes in these directories: ['.../part-1-apis/01-your-first-api']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [11038] using WatchFiles
INFO:     Started server process [11041]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     127.0.0.1:55554 - "GET / HTTP/1.1" 200 OK
INFO:     127.0.0.1:55556 - "GET /hello/Sam HTTP/1.1" 200 OK
INFO:     127.0.0.1:55568 - "GET /add?a=2&b=3 HTTP/1.1" 200 OK
```
In the browser, one page per address:
```
/              →  {"message":"Hello! My API works."}
/hello/Sam     →  {"message":"Hi Sam, nice to meet you!"}
/add?a=2&b=3   →  {"a":2.0,"b":3.0,"answer":5.0}
```
Look at the terminal: every visit adds a line with the address and `200 OK` (200 is the web's code for "success"). At `/docs` you get a page listing all 3 endpoints. Click one → **Try it out** → fill in the boxes → **Execute** to call it without typing addresses.

## How it works
```
browser ──"GET /add?a=2&b=3"──▶ uvicorn (server) ──▶ FastAPI finds add() ──▶ add(a=2.0, b=3.0)
browser ◀──── {"answer": 5.0} ── uvicorn ◀──── FastAPI turns the dict into JSON ◀───┘
```
1. `from fastapi import FastAPI` and `app = FastAPI()` create your API. `app` is the object uvicorn looks for (that's the `app` in `main:app`).
2. `@app.get("/")` above `def home():` is a **decorator**: a label that says "when someone visits `/` with a GET request (a normal browser visit), run this function". `home()` returns a Python dictionary; FastAPI turns it into JSON for you.
3. `@app.get("/hello/{name}")`: the `{name}` part is a blank to fill in. Visiting `/hello/Sam` calls `hello(name="Sam")`. The `name: str` is a **type hint**: it tells FastAPI to expect text.
4. `@app.get("/add")` with `def add(a: float, b: float)`: because `a` and `b` are not in the path, FastAPI reads them from the **query string** (`?a=2&b=3`). `float` means "a number that may have decimals", so FastAPI converts the text `"2"` into the number `2.0`. That's why you see `5.0`, not `5`.
5. If an input can't be converted (say `b=hello`), FastAPI refuses before your function even runs and sends back a clear error. That's **validation**, for free.
6. `127.0.0.1` means "this computer" and `8000` is the **port** (a numbered door on your computer). Only you can visit it for now. Lesson 05 puts it on the internet.

## If something goes wrong
- **`uvicorn: command not found` / `'uvicorn' is not recognized`** → your venv is off or the install line wasn't run. Switch the venv on and run the pip line again. You can also start it with `python -m uvicorn main:app --reload`.
- **`Error loading ASGI app. Could not import module "main"`** → you're not in the lesson folder. Run `cd part-1-apis/01-your-first-api` from the course folder first.
- **`error while attempting to bind on address ('127.0.0.1', 8000): address already in use`** (the error number differs per system: 98, 48 or 10048) → another server is still running on port 8000 (maybe in another terminal). Stop it with Ctrl + C, or use another port: `uvicorn main:app --reload --port 8001` and visit `http://127.0.0.1:8001`.
- **The browser says "This site can't be reached"** → the server isn't running. Check the terminal still shows `Uvicorn running`, and that you typed `http://` (not `https://`).
- **You saved a change but the page didn't change** → refresh the browser. If the terminal shows a red error after saving, fix the line it points to and save again.

## Try this
1. Add a `/goodbye` address that returns `{"message": "Bye!"}`. Save the file; `--reload` restarts the server for you.
2. Add `/multiply?a=4&b=5` that returns the product. Then visit `/add?a=2&b=hello` and read the error FastAPI sends.
3. Add `/greet/{name}` with an optional query parameter `excited` that defaults to `False`. `/greet/Sam` should say `Hi Sam`; `/greet/Sam?excited=true` should say `HI SAM!!!`.

<details><summary>Solutions</summary>

Add these to the end of `main.py`:
```python
@app.get("/goodbye")
def goodbye():
    return {"message": "Bye!"}


@app.get("/multiply")
def multiply(a: float, b: float):
    return {"a": a, "b": b, "answer": a * b}


# A parameter with a default value (= False) becomes optional.
@app.get("/greet/{name}")
def greet(name: str, excited: bool = False):
    message = f"Hi {name}"
    if excited:
        message = message.upper() + "!!!"
    return {"message": message}
```
`/multiply?a=4&b=5` gives `{"a":4.0,"b":5.0,"answer":20.0}`. The `b=hello` error says `"Input should be a valid number, unable to parse string as a number"`, with status code 422 ("I understood you, but your input is wrong").
</details>

## Check yourself
1. What does `@app.get("/hello/{name}")` do, in one sentence?
2. In `/add?a=2&b=3`, why does the answer come back as `5.0` and not `5`?
3. Why does the server keep running after you start it, instead of finishing like `hello.py` did?
4. What would you change to make `/add` work only with whole numbers?

<details><summary>Answers</summary>

1. It connects the address `/hello/<something>` to the function below it, passing `<something>` in as `name`.
2. The type hints say `a: float, b: float`, so FastAPI converts the inputs to decimal numbers, and 2.0 + 3.0 = 5.0.
3. A server's job is to wait for visitors. It keeps listening until you stop it with Ctrl + C.
4. Change the type hints to `a: int, b: int`. Then `a=2.5` would be refused with a validation error.
</details>

## Learn more (optional)
- FastAPI's official tutorial, "First Steps": https://fastapi.tiangolo.com/tutorial/first-steps/
- What is JSON? (MDN): https://developer.mozilla.org/en-US/docs/Learn_web_development/Core/Scripting/JSON
- Video: search YouTube for "FastAPI tutorial for beginners" or "what is an API".

## Next
→ [02 · To-do list API](../02-todo-list-api)
