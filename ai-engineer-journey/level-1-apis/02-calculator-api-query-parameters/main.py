"""Project 1.2: a calculator API using query parameters (?a=2&b=3)."""
from fastapi import FastAPI, HTTPException

app = FastAPI(title="Calculator API")


@app.get("/add")
def add(a: float, b: float):
    # /add?a=2&b=3 -> FastAPI reads a and b from the URL and converts them to floats
    return {"operation": "add", "a": a, "b": b, "result": a + b}


@app.get("/subtract")
def subtract(a: float, b: float):
    return {"operation": "subtract", "a": a, "b": b, "result": a - b}


@app.get("/multiply")
def multiply(a: float, b: float):
    return {"operation": "multiply", "a": a, "b": b, "result": a * b}


@app.get("/divide")
def divide(a: float, b: float):
    if b == 0:
        # 400 = "Bad Request": the caller sent something we can't handle
        raise HTTPException(status_code=400, detail="Cannot divide by zero")
    return {"operation": "divide", "a": a, "b": b, "result": a / b}
