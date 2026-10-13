"""Project 1.5: the same to-do API as 1.4, but tasks survive restarts because they live in a database."""
from datetime import datetime

from fastapi import Depends, FastAPI, HTTPException, Response
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.orm import Session

from database import Base, engine, get_db
from models import TodoRow

Base.metadata.create_all(bind=engine)   # create the table if it doesn't exist yet
app = FastAPI(title="To-do API (database)")


class TodoCreate(BaseModel):
    title: str = Field(min_length=1, max_length=200)
    done: bool = False


class TodoUpdate(BaseModel):
    title: str | None = Field(default=None, min_length=1, max_length=200)
    done: bool | None = None


class Todo(TodoCreate):
    model_config = ConfigDict(from_attributes=True)   # lets Pydantic read SQLAlchemy objects
    id: int
    created_at: datetime


def find(db: Session, todo_id: int) -> TodoRow:
    row = db.get(TodoRow, todo_id)
    if row is None:
        raise HTTPException(404, f"Todo {todo_id} not found")
    return row


@app.post("/todos", response_model=Todo, status_code=201)
def create_todo(data: TodoCreate, db: Session = Depends(get_db)):
    row = TodoRow(**data.model_dump())
    db.add(row)
    db.commit()          # write to disk
    db.refresh(row)      # read back the id the database assigned
    return row


@app.get("/todos", response_model=list[Todo])
def list_todos(done: bool | None = None, db: Session = Depends(get_db)):
    query = select(TodoRow).order_by(TodoRow.id)   # SQL: SELECT * FROM todos ORDER BY id
    if done is not None:
        query = query.where(TodoRow.done == done)  # ... WHERE done = ?
    return db.scalars(query).all()


@app.get("/todos/{todo_id}", response_model=Todo)
def get_todo(todo_id: int, db: Session = Depends(get_db)):
    return find(db, todo_id)


@app.patch("/todos/{todo_id}", response_model=Todo)
def update_todo(todo_id: int, changes: TodoUpdate, db: Session = Depends(get_db)):
    row = find(db, todo_id)
    for field, value in changes.model_dump(exclude_unset=True).items():
        setattr(row, field, value)
    db.commit()
    db.refresh(row)
    return row


@app.delete("/todos/{todo_id}", status_code=204)
def delete_todo(todo_id: int, db: Session = Depends(get_db)):
    db.delete(find(db, todo_id))
    db.commit()
    return Response(status_code=204)
