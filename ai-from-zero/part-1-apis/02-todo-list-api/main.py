# A to-do list API: add, view, finish and delete tasks. Tasks live in a Python list (memory).
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

app = FastAPI()
tasks = []          # our "storage": a plain list
next_id = 1


class NewTask(BaseModel):     # describes what a new task must look like: {"title": "..."}
    title: str


@app.get("/tasks")                       # GET = "show me"
def list_tasks():
    return tasks


@app.post("/tasks")                      # POST = "create something new"
def add_task(task: NewTask):
    global next_id
    new = {"id": next_id, "title": task.title, "done": False}
    tasks.append(new)
    next_id += 1
    return new


@app.put("/tasks/{task_id}/done")        # PUT = "change something"
def finish_task(task_id: int):
    for task in tasks:
        if task["id"] == task_id:
            task["done"] = True
            return task
    raise HTTPException(status_code=404, detail="No task with that id")   # 404 = "not found"


@app.delete("/tasks/{task_id}")          # DELETE = "remove it"
def delete_task(task_id: int):
    for task in tasks:
        if task["id"] == task_id:
            tasks.remove(task)
            return {"deleted": task_id}
    raise HTTPException(status_code=404, detail="No task with that id")
