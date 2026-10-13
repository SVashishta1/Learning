# 1.4 · To-do API: CRUD in memory

**What you build:** create, read, update and delete tasks. These four actions (**CRUD**) are behind almost every app you use.
**Like you're 10:** a notebook. Write a task (Create), look at it (Read), tick it off (Update), tear out the page (Delete).

## Run it
```bash
cd level-1-apis/04-todo-api-crud-in-memory
pip install -r requirements.txt
uvicorn main:app --reload
```
Use http://127.0.0.1:8000/docs to: POST a todo → GET /todos → PATCH it `{"done": true}` → DELETE it.

With curl:
```bash
curl -X POST localhost:8000/todos -H "Content-Type: application/json" -d '{"title":"buy milk"}'
curl localhost:8000/todos
curl -X PATCH localhost:8000/todos/1 -H "Content-Type: application/json" -d '{"done":true}'
curl -X DELETE localhost:8000/todos/1 -i
```
Test: `pytest -v`

## Key ideas
| CRUD | HTTP verb | Route | Success code |
|------|-----------|-------|--------------|
| Create | POST | `/todos` | 201 Created |
| Read | GET | `/todos`, `/todos/{id}` | 200 OK |
| Update | PATCH | `/todos/{id}` | 200 OK |
| Delete | DELETE | `/todos/{id}` | 204 No Content |

- **Three Pydantic models** for one thing (`TodoCreate`, `TodoUpdate`, `Todo`): what clients send is different from what you return. That is real-world API design.
- `exclude_unset=True` means "only apply fields the client actually sent".

## Your turn
1. Add `priority: int = Field(1, ge=1, le=3)` and sort `GET /todos` by priority.
2. Add `GET /todos/stats` returning `{"total": 5, "done": 2}`.
3. Restart the server. Your todos are gone! Why? (→ next project)

## Watch
- REST APIs explained: https://www.youtube.com/results?search_query=REST+API+crud+explained+beginners
