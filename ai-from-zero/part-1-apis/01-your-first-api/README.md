# 01 · Your first API

**What it does:** turns 3 small Python functions into web addresses your browser can visit.

## Run it
```bash
cd part-1-apis/01-your-first-api
uvicorn main:app --reload
```
Leave that terminal running, then open these in your browser:
- http://127.0.0.1:8000/ → `{"message": "Hello! My API works."}`
- http://127.0.0.1:8000/hello/Sam
- http://127.0.0.1:8000/add?a=2&b=3 → `"answer": 5.0`
- http://127.0.0.1:8000/docs → a **free control panel** where you can try every address with buttons

Stop the server with `Ctrl + C`.

## The idea in one sentence
`@app.get("/hello/{name}")` means "when someone visits this address, run the function below and send back its answer as JSON (text that programs can read)".

## Try this
1. Add a `/goodbye` address that returns `{"message": "Bye!"}`. Save the file; `--reload` restarts the server for you.
2. Add `/multiply?a=4&b=5`.
3. Visit `/add?a=2&b=hello`. Read the error: FastAPI checks your inputs for you!
