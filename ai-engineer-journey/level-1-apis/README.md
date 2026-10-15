# Level 1 · APIs: a restaurant menu for programs

An **API** is a restaurant menu for programs. The menu lists what you can order (**routes** like `/add`).
You place an order (a **request**), the kitchen cooks (your **Python function**), and the waiter brings back a dish (the **response**, usually **JSON**).

Every AI product you'll build later (chatbots, RAG apps, agents) sits behind an API like these.

| # | Project | New idea you learn |
|---|---------|--------------------|
| 1.1 | [Hello API](01-hello-api-the-waiter-says-hi) | routes, JSON, auto docs |
| 1.2 | [Calculator API](02-calculator-api-query-parameters) | query parameters, errors, tests |
| 1.3 | [Joke & quote API](03-joke-and-quote-api-random-picks) | path params, POST bodies, Pydantic |
| 1.4 | [To-do API](04-todo-api-crud-in-memory) | CRUD, status codes |
| 1.5 | [To-do + database](05-todo-api-with-sqlite-then-postgres) | SQL, ORM, persistence |
| 1.6 | [Login API](06-login-api-hashed-passwords-and-jwt) | hashing, JWT auth, protected routes |
| 1.7 | [Dockerize & deploy](07-dockerize-and-deploy-to-the-cloud) | containers, env vars, cloud deploy |
| 1.8 | [Call other APIs](08-weather-proxy-calling-other-apis) | being a *client*: timeouts, retries, caching (exactly what LLM APIs need) |

**How each project works:** `cd` into its folder, `pip install -r requirements.txt` (with your venv from 0.1 active), start it with `uvicorn main:app --reload`, play with it at http://127.0.0.1:8000/docs, and run `pytest -v` (from 1.2 on). No API keys are needed anywhere in this level.

**Extra tools:** Docker Desktop for 1.5 Part B (or an installed PostgreSQL) and for 1.7; a free Render account for deploying in 1.7.

**Finish line for Level 1:** your login + to-do API is live on a public URL. 🎉 Then go to [Level 2 · Neural nets from scratch](../level-2-neural-nets-from-scratch).
