# The same to-do API, but tasks are saved in a DATABASE file (tasks.db), so they survive restarts.
# sqlite3 comes with Python: nothing to install. SQL is the language for talking to databases.
import sqlite3

from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()
db = sqlite3.connect("tasks.db", check_same_thread=False)
db.row_factory = sqlite3.Row                 # lets us read rows like dictionaries
db.execute("CREATE TABLE IF NOT EXISTS tasks (id INTEGER PRIMARY KEY, title TEXT, done INTEGER DEFAULT 0)")


class NewTask(BaseModel):
    title: str


@app.get("/tasks")
def list_tasks():
    rows = db.execute("SELECT * FROM tasks").fetchall()
    return [dict(row) for row in rows]


@app.post("/tasks")
def add_task(task: NewTask):
    # The ? is filled in safely by sqlite. Never glue user text straight into SQL (that's how databases get hacked).
    cursor = db.execute("INSERT INTO tasks (title) VALUES (?)", (task.title,))
    db.commit()                               # commit = "save to disk now"
    return {"id": cursor.lastrowid, "title": task.title, "done": 0}


@app.put("/tasks/{task_id}/done")
def finish_task(task_id: int):
    changed = db.execute("UPDATE tasks SET done = 1 WHERE id = ?", (task_id,)).rowcount
    db.commit()
    if changed == 0:
        raise HTTPException(404, "No task with that id")
    return {"id": task_id, "done": 1}


@app.delete("/tasks/{task_id}")
def delete_task(task_id: int):
    removed = db.execute("DELETE FROM tasks WHERE id = ?", (task_id,)).rowcount
    db.commit()
    if removed == 0:
        raise HTTPException(404, "No task with that id")
    return {"deleted": task_id}


@app.get("/tasks/search")
def search(word: str):
    rows = db.execute("SELECT * FROM tasks WHERE title LIKE ?", (f"%{word}%",)).fetchall()
    return [dict(row) for row in rows]
