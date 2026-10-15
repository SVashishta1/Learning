# Part 1 · APIs

**An API is a menu for programs.** Your program asks for something ("give me the weather in Paris"), and another program answers with data. Every AI app you'll build later sits behind one, and talking to an AI like Claude is just calling its API.

**Time:** about 1 week at 1 hour a day · **Before this part:** finish [00 · Start here](../00-start-here) (Python, venv and editor set up)

| # | Project | What you'll have at the end |
|---|---------|-----------------------------|
| 01 | [Your first API](01-your-first-api) | a web address that answers you, and a free test page |
| 02 | [To-do list API](02-todo-list-api) | add, view, finish and delete tasks (CRUD) |
| 03 | [Save to a database](03-api-that-saves-to-a-database) | tasks that survive a restart, stored with SQL |
| 04 | [Your code calls another API](04-your-code-calls-another-api) | live weather for any city |
| 05 | [Put your API on the internet](05-put-your-api-on-the-internet) | a link you can open on your phone |

## Install once for this part
Open a terminal in the course folder (`ai-from-zero`), switch your venv on ([00 · Start here](../00-start-here), step 6), then:
```bash
pip install fastapi "uvicorn[standard]" httpx
```
- `fastapi`: turns Python functions into web addresses (it also installs `pydantic`, which checks inputs).
- `uvicorn[standard]`: the server that runs your API. Keep the quotes: some terminals treat `[ ]` specially.
- `httpx`: lets your code call other APIs (lesson 04).

Lesson 05 also uses Docker Desktop (optional) or a free Render account. Its README explains both.

## After this part you'll be able to
- Build a web API in Python with FastAPI, and test it from the automatic `/docs` page.
- Explain GET, POST, PUT and DELETE, status codes like 200, 404 and 422, and JSON.
- Save and search data in a SQLite database with safe SQL queries.
- Call someone else's API from Python and pick values out of the JSON it returns.
- Package an API in a Docker container and put it online with a shareable link.

**Every lesson works the same way:** `cd` into its folder from the course folder, run the command in its README, compare with "What you should see", then read the code alongside "How it works".

## Next
Start with → [01 · Your first API](01-your-first-api). When you finish lesson 05, go on to → [Part 2 · Machine learning](../part-2-machine-learning).
