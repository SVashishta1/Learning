# Your first API. Run it, then open http://127.0.0.1:8000 in your browser.
from fastapi import FastAPI

app = FastAPI()


# "When someone visits / , run this function and send back what it returns."
@app.get("/")
def home():
    return {"message": "Hello! My API works."}


# {name} is a blank to fill in: /hello/Sam -> name = "Sam"
@app.get("/hello/{name}")
def hello(name: str):
    return {"message": f"Hi {name}, nice to meet you!"}


# ?a=2&b=3 at the end of the address -> a = 2, b = 3
@app.get("/add")
def add(a: float, b: float):
    return {"a": a, "b": b, "answer": a + b}
