# 1.1 · Hello API: the waiter says hi

**What you'll build:** a tiny web API with two routes: `/` answers `{"message": "Hello"}` and `/hello/Sam` answers `{"message": "Hello, Sam! 👋"}`.
**Like you're 10:** you open a restaurant with one thing on the menu. Anyone who walks in gets a "Hello" from the waiter.
**Time:** ~30 min · **Builds on:** [0.2 · Python for AI warm-up](../../level-0-setup/02-python-for-ai-warmup) · **Needs:** nothing extra

## Why this matters
Every AI product you use (ChatGPT, Claude, a RAG search box) is an API underneath: a program waiting for requests and sending back JSON. Companies hire AI engineers to put models *behind* APIs so apps and websites can use them. This is the smallest possible version of that job.

## What you'll learn
- **API:** a menu of things a program can ask another program for, over the web.
- **Route (endpoint):** one address on the menu, like `/hello/{name}`.
- **GET request:** "give me something". Your browser sends one every time you open a URL.
- **JSON:** the text format APIs speak: `{"key": "value"}`. A Python dict becomes JSON automatically.
- **Server and port:** the server (uvicorn) is the program that waits for requests; the port (8000) is which "door" of your computer it listens on.

## Before you start
```bash
cd level-1-apis/01-hello-api-the-waiter-says-hi
pip install -r requirements.txt
```
- `fastapi`: turns Python functions into web routes.
- `uvicorn[standard]`: the server that runs your FastAPI app.

No API key needed.

## Run it
1. Start the server (from the folder above, with your venv active):
   ```bash
   uvicorn main:app --reload
   ```
   `main:app` means "in the file `main.py`, find the variable `app`". `--reload` restarts the server every time you save a file.
2. Open these in your browser:
   - http://127.0.0.1:8000/
   - http://127.0.0.1:8000/hello/Sam
   - http://127.0.0.1:8000/docs (free interactive docs: click a route, **Try it out**, **Execute**)
3. Or, in a **second** terminal: `curl http://127.0.0.1:8000/hello/Sam`
4. Stop the server with `Ctrl+C`.

### What you should see
In the terminal running uvicorn:
```
INFO:     Will watch for changes in these directories: ['.../01-hello-api-the-waiter-says-hi']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [11331] using WatchFiles
INFO:     Started server process [11334]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
INFO:     127.0.0.1:60848 - "GET / HTTP/1.1" 200 OK
INFO:     127.0.0.1:60850 - "GET /hello/Sam HTTP/1.1" 200 OK
```
In the browser (or curl):
```
{"message":"Hello"}
{"message":"Hello, Sam! 👋"}
```
Each request shows up as a log line: the method (`GET`), the path, and the status code (`200 OK` = it worked).

## How it works
```
browser ──GET /hello/Sam──► uvicorn (port 8000) ──► FastAPI finds the route ──► greet("Sam")
browser ◄──{"message": "Hello, Sam! 👋"}── JSON ◄── returns a dict ◄─────────────┘
```
1. `app = FastAPI(title=..., description=...)` creates the application. The title and description appear on `/docs`.
2. `@app.get("/")` is a **decorator**: a label on the next function that says "when someone sends GET to `/`, run me". So `say_hello()` runs for http://127.0.0.1:8000/.
3. `say_hello()` returns a Python dict. FastAPI converts it to JSON and sends it back.
4. `@app.get("/hello/{name}")` has a **path parameter**: whatever is in the URL where `{name}` is gets passed to `greet(name)`. Because of the type hint `name: str`, FastAPI knows it's text.
5. `/docs` is built automatically from your routes and type hints. You wrote zero lines for it.

## If something goes wrong
- **`ModuleNotFoundError: No module named 'fastapi'`** or **`uvicorn: command not found`** → your venv isn't active, or you didn't install. Activate it (see 0.1) and re-run `pip install -r requirements.txt`.
- **`Error loading ASGI app. Could not import module "main"`** → you're in the wrong folder. `cd` into `01-hello-api-the-waiter-says-hi` first.
- **`[Errno 48] Address already in use`** (or `Errno 98`, or "only one usage of each socket address" on Windows) → another server is still running on port 8000. Stop it with `Ctrl+C`, or use another port: `uvicorn main:app --reload --port 8001`.
- **The browser says "This site can't be reached"** → the server isn't running (check the terminal for errors), or you typed `https://` instead of `http://`.
- **`{"detail":"Not Found"}`** → the server works, but no route matches that path. Check spelling and capital letters.

## Try this
1. Add `/goodbye` that returns `{"message": "Bye!"}`.
   <details><summary>Solution</summary>

   ```python
   @app.get("/goodbye")
   def goodbye():
       return {"message": "Bye!"}
   ```
   Save the file; `--reload` restarts the server for you. Visit http://127.0.0.1:8000/goodbye.
   </details>
2. Add `/age/{years}` that returns `{"dog_years": years * 7}`. Use `years: int` so FastAPI checks it's a number. What happens at `/age/abc`?
   <details><summary>Solution</summary>

   ```python
   @app.get("/age/{years}")
   def dog_years(years: int):
       return {"dog_years": years * 7}
   ```
   `/age/3` gives `{"dog_years":21}`. `/age/abc` gives status **422 Unprocessable Content** with `"msg":"Input should be a valid integer, unable to parse string as an integer"`. FastAPI checked the type for you before your function ran.
   </details>
3. Stop the server with `Ctrl+C`, start it on port 9000, and add a query parameter: `/hello/{name}?shout=true` returns the greeting in capitals.
   <details><summary>Solution</summary>

   Start with `uvicorn main:app --reload --port 9000`. Then change `greet`:
   ```python
   @app.get("/hello/{name}")
   def greet(name: str, shout: bool = False):
       message = f"Hello, {name}! 👋"
       return {"message": message.upper() if shout else message}
   ```
   Function arguments that are **not** in the path become query parameters (after `?`). You'll use these a lot in 1.2.
   </details>

## Check yourself
1. In `uvicorn main:app`, what are `main` and `app`?
2. What does `@app.get("/hello/{name}")` do to the function under it?
3. You return a Python dict. What does the browser actually receive?
4. What does status code 200 mean, and where did you see it?

<details><summary>Answers</summary>

1. `main` is the file `main.py`; `app` is the FastAPI object inside it.
2. It registers the function as the handler for GET requests to `/hello/<something>`, and passes `<something>` in as `name`.
3. JSON text, like `{"message":"Hello"}`. FastAPI converts the dict for you.
4. 200 means "OK, it worked". You saw it in uvicorn's log lines (`"GET / HTTP/1.1" 200 OK`).
</details>

## Learn more (optional)
- FastAPI official tutorial (read the first 3 pages): https://fastapi.tiangolo.com/tutorial/first-steps/
- What is an API? (simple explanation): https://www.youtube.com/results?search_query=what+is+an+API+explained+simply

## Next
→ [1.2 · Calculator API: query parameters + first tests](../02-calculator-api-query-parameters)
