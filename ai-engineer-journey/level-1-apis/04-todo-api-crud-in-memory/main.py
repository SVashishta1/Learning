"""Project 1.4: a to-do API with full CRUD (Create, Read, Update, Delete), stored in a list."""
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Response
from pydantic import BaseModel, Field

app = FastAPI(title="To-do API (in memory)")


class TodoCreate(BaseModel):          # what the client SENDS to create a task
    title: str = Field(min_length=1, max_length=200)
    done: bool = False


class TodoUpdate(BaseModel):          # every field optional: PATCH changes only what you send
    title: str | None = Field(default=None, min_length=1, max_length=200)
    done: bool | None = None


class Todo(TodoCreate):               # what the API RETURNS (adds id + timestamp)
    id: int
    created_at: datetime


todos: list[Todo] = []
next_id = 1


def find(todo_id: int) -> Todo:
    for t in todos:
        if t.id == todo_id:
            return t
    raise HTTPException(status_code=404, detail=f"Todo {todo_id} not found")


@app.post("/todos", response_model=Todo, status_code=201)      # C: create
def create_todo(data: TodoCreate):
    global next_id
    todo = Todo(id=next_id, created_at=datetime.now(timezone.utc), **data.model_dump())
    todos.append(todo)
    next_id += 1
    return todo


@app.get("/todos", response_model=list[Todo])                  # R: read all (with optional filter)
def list_todos(done: bool | None = None):
    return [t for t in todos if done is None or t.done == done]


@app.get("/todos/{todo_id}", response_model=Todo)              # R: read one
def get_todo(todo_id: int):
    return find(todo_id)


@app.patch("/todos/{todo_id}", response_model=Todo)            # U: update
def update_todo(todo_id: int, changes: TodoUpdate):
    todo = find(todo_id)
    # exclude_unset: only fields the client actually sent. exclude_none: treat null as "leave it alone".
    for field, value in changes.model_dump(exclude_unset=True, exclude_none=True).items():
        setattr(todo, field, value)
    return todo


@app.delete("/todos/{todo_id}", status_code=204)               # D: delete
def delete_todo(todo_id: int):
    todos.remove(find(todo_id))
    return Response(status_code=204)                           # 204 = done, nothing to return
