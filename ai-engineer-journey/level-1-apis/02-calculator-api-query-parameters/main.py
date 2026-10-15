"""Project 1.2: a calculator API using query parameters (?a=2&b=3)."""
import math

from fastapi import FastAPI, HTTPException

app = FastAPI(title="Calculator API")


def answer(operation: str, a: float, b: float, result: float) -> dict:
    # JSON has no way to write "infinity" or "not a number", so refuse them with a clear 400
    # instead of crashing with a 500. Try /multiply?a=1e308&b=10 to see it.
    if not math.isfinite(result):
        raise HTTPException(status_code=400, detail="Result is not a finite number")
    return {"operation": operation, "a": a, "b": b, "result": result}


@app.get("/add")
def add(a: float, b: float):
    # /add?a=2&b=3 -> FastAPI reads a and b from the URL and converts them to floats
    return answer("add", a, b, a + b)


@app.get("/subtract")
def subtract(a: float, b: float):
    return answer("subtract", a, b, a - b)


@app.get("/multiply")
def multiply(a: float, b: float):
    return answer("multiply", a, b, a * b)


@app.get("/divide")
def divide(a: float, b: float):
    if b == 0:
        # 400 = "Bad Request": the caller sent something we can't handle
        raise HTTPException(status_code=400, detail="Cannot divide by zero")
    return answer("divide", a, b, a / b)
