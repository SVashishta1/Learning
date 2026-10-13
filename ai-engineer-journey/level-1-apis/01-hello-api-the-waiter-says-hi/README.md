# 1.1 · Hello API: the waiter says hi

**What you build:** a web API with one route that returns `{"message": "Hello"}`.
**Like you're 10:** you open a restaurant with exactly one thing on the menu. When anyone walks in, the waiter says "Hello".

## Run it (5 minutes)
```bash
cd level-1-apis/01-hello-api-the-waiter-says-hi
pip install -r requirements.txt
uvicorn main:app --reload
```
- `main:app` means: in the file `main.py`, find the variable `app`.
- `--reload` restarts the server every time you save a file.

Now open:
- http://127.0.0.1:8000/ shows `{"message":"Hello"}`
- http://127.0.0.1:8000/hello/Sam shows `{"message":"Hello, Sam! 👋"}`
- http://127.0.0.1:8000/docs is **free interactive docs** FastAPI builds for you. Click "Try it out".

Or from a terminal: `curl http://127.0.0.1:8000/hello/Sam`

## Key ideas
| Word | Meaning |
|------|---------|
| **route / endpoint** | an address on the menu, like `/hello/{name}` |
| **GET** | "give me something" (other verbs: POST create, PUT/PATCH change, DELETE remove) |
| **JSON** | the language APIs speak: `{"key": "value"}` |
| **server** | the program waiting for requests (uvicorn) |
| **port 8000** | which "door" of your computer the server listens on |

## Your turn
1. Add `/goodbye` that returns `{"message": "Bye!"}`.
2. Add `/age/{years}` that returns `{"dog_years": years * 7}`. Use `years: int` so FastAPI checks it's a number. What happens at `/age/abc`?
3. Stop the server with `Ctrl+C`, change the port with `--port 9000`, and visit it.

## Watch
- FastAPI official tutorial (read the first 3 pages): https://fastapi.tiangolo.com/tutorial/first-steps/
- What is an API? (simple explanation): https://www.youtube.com/results?search_query=what+is+an+API+explained+simply
