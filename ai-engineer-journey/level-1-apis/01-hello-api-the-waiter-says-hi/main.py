"""Project 1.1: the smallest useful API.

FastAPI turns ordinary Python functions into web endpoints.
The decorator @app.get("/") means: "when someone visits / with GET, run this function".
"""
from fastapi import FastAPI

app = FastAPI(title="Hello API", description="The waiter says hi.")


@app.get("/")
def say_hello():
    # Returning a dict -> FastAPI turns it into JSON: {"message": "Hello"}
    return {"message": "Hello"}


@app.get("/hello/{name}")
def greet(name: str):
    # {name} in the path becomes the function argument
    return {"message": f"Hello, {name}! 👋"}
