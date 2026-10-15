# 10 · Save a model and serve it as an API

**What you'll build:** you train the house-price model once, save it to a file, and then run a web API that gives anyone a price estimate in milliseconds. This is how machine-learning models are used in real apps.
**Time:** ~40 min · **Builds on:** [06 · Predict house prices](../06-predict-house-prices) and [01 · Your first API](../../part-1-apis/01-your-first-api) · **Needs:** nothing extra

Like you're 10: a chef spends years learning to cook (training), but at the restaurant they just cook your order in minutes (predicting). You don't send the chef back to school for every meal.

## Why this matters
A model that only lives inside a script is a toy. In real products, training happens once (or once a night), the trained model is saved as a file, and a separate API loads that file and answers prediction requests from apps and websites. This "train → save → serve" split is the core of **MLOps**, the job of putting models into production, and it's exactly how the AI services in Parts 4–6 are offered to you.

## What you'll learn
- **Training vs. inference**: learning from examples (slow, done once) vs. using what was learned to answer (fast, done many times). Using a model is called **inference**.
- **Saving a model**: `joblib.dump` writes the trained model to a file; `joblib.load` reads it back, ready to use.
- **Serving a model**: wrapping `model.predict` in an API endpoint, so other programs can use it over the web.
- **Input validation**: `Field(gt=10, lt=2000)` rejects nonsense like a -5 m² house before it reaches the model.

## Before you start
- Venv on, and this part's install line done (skip if done already):
  ```bash
  pip install scikit-learn joblib fastapi "uvicorn[standard]"
  ```
  - `scikit-learn`: trains the model.
  - `joblib`: saves and loads the trained model as a file.
  - `fastapi` and `uvicorn[standard]`: build and run the API (as in Part 1).
- No API key needed.

## Run it
1. From the course folder (`ai-from-zero`), go to the lesson and **train once**:
   ```bash
   cd part-2-machine-learning/10-save-a-model-and-serve-it
   python train.py
   ```
   A new file appears in the folder: `house_model.joblib`. That's the trained model.
2. **Serve it:**
   ```bash
   uvicorn api:app --reload
   ```
3. Open http://127.0.0.1:8000/docs → **POST /predict** → **Try it out** → replace the body with:
   ```json
   {"size_m2": 120, "bedrooms": 3, "km_to_centre": 5}
   ```
   → **Execute**.
4. Stop the server with **Ctrl + C** when done.

### What you should see
`python train.py` prints:
```
Saved house_model.joblib. Now run: uvicorn api:app --reload
```
The API's **Response body**:
```
{"size_m2": 120, "bedrooms": 3, "km_to_centre": 5}   →  {"estimated_price": 359000}
{"size_m2": 200, "bedrooms": 4, "km_to_centre": 2}   →  {"estimated_price": 583000}
{"size_m2": -5, "bedrooms": 3, "km_to_centre": 5}    →  {"detail": [{"type": "greater_than", "loc": ["body", "size_m2"], "msg": "Input should be greater than 10", ...}]}   (code 422)
```
The first answer matches lesson 06's estimate ($359,814), rounded to the nearest thousand. The terminal shows each request, like `"POST /predict HTTP/1.1" 200 OK`. Training took a moment; each prediction now takes about a millisecond.

## How it works
```
ONCE:        train.py ──fit──▶ model ──joblib.dump──▶ house_model.joblib (file)
                                                             │
SERVER START: api.py ──joblib.load─────────────────────────┘ (model kept in memory)

EVERY REQUEST: app ──POST /predict {"size_m2": 120, ...}──▶ House checks inputs ──▶ model.predict ──▶ {"estimated_price": 359000}
```
**`train.py`**
1. Makes the same 500 example houses as lesson 06 (same `random.seed(1)` and same hidden rule).
2. `LinearRegression().fit(houses, prices)` trains on all 500 houses. (Lesson 06 already checked how good this kind of model is, so here we use every example.)
3. `model_file = Path(__file__).parent / "house_model.joblib"` builds the path "next to this file". `Path(__file__).parent` means "the folder this script is in", so the file lands in the lesson folder wherever you run it from.
4. `joblib.dump(model, model_file)` saves the trained model. It's a small file (under 1 KB here) holding the learned numbers.

**`api.py`**
1. `MODEL_FILE` points to the same file. If it doesn't exist, `raise SystemExit(...)` stops the server with a clear message instead of a confusing error.
2. `model = joblib.load(MODEL_FILE)` loads the model **once**, when the server starts. Loading it on every request would be slow and wasteful.
3. `class House(BaseModel)` describes the request body. `Field(gt=10, lt=2000)` means "greater than 10 and less than 2000"; `ge` and `le` mean "greater/less than or equal". Bad inputs get a 422 error and never reach the model. Real models give silly answers to silly inputs (see lesson 06's negative price), so this guard matters.
4. `predict(house)` builds the same `[[size, bedrooms, km]]` shape the model was trained with (same order!), calls `model.predict`, and returns the price rounded to the nearest 1,000 with `round(price, -3)`. `int(...)` turns it into a whole number so the JSON shows `359000`, not `359000.0`.

## If something goes wrong
- **`No house_model.joblib yet. Run python train.py first`** → you started the server before training. Run `python train.py` in this folder, then start `uvicorn` again.
- **`Could not import module "api"`** → you're not in the lesson folder, or you typed `main:app`. This lesson's file is `api.py`, so the command is `uvicorn api:app --reload`.
- **You retrained but the API gives the old answers** → the model is loaded only when the server starts, and `--reload` only watches `.py` files. Stop the server (Ctrl + C) and start it again.
- **`InconsistentVersionWarning: Trying to unpickle estimator LinearRegression from version ...`** → the model file was saved with a different scikit-learn version than the one loading it (common after an upgrade, or inside Docker). Run `python train.py` again with the current version.
- **`address already in use`** → another server (maybe from Part 1) is still running. Stop it, or add `--port 8001`.

## Try this
1. Send `"size_m2": -5`, then `"bedrooms": 50`. Read the error messages. Which `Field` rule caught each one?
2. Make the API "learn" a new market: change the hidden rule in `train.py` to `5_000 * size`, retrain, and get a new estimate for the same 120 m² house, without touching `api.py`.
3. Put this model API in a Docker container, using the pattern from [lesson 05](../../part-1-apis/05-put-your-api-on-the-internet).

<details><summary>Hints and solutions</summary>

1. `-5` breaks `size_m2: float = Field(gt=10, lt=2000)` ("Input should be greater than 10"). `50` bedrooms breaks `bedrooms: int = Field(ge=0, le=20)` ("Input should be less than or equal to 20").
2. In `train.py`, change `2_500 * size` to `5_000 * size`. Run `python train.py`, then **restart** the server (Ctrl + C, then `uvicorn api:app --reload`). The same house now gives `{"estimated_price": 659000}`. This is the whole point of the split: retraining only changes the file; the API code stays the same.
3. Create a file named `Dockerfile` in this folder:
   ```dockerfile
   FROM python:3.12-slim
   WORKDIR /app
   RUN pip install --no-cache-dir scikit-learn joblib fastapi "uvicorn[standard]"
   COPY train.py api.py ./
   # Train inside the box, so the model file matches the box's scikit-learn version.
   RUN python train.py
   CMD ["sh", "-c", "exec uvicorn api:app --host 0.0.0.0 --port ${PORT:-8000}"]
   ```
   Then run `docker build -t house-api .` and `docker run -p 8000:8000 house-api`, and open http://localhost:8000/docs. **POST /predict** gives `{"estimated_price": 359000}`, the same as before. You could deploy this folder to Render exactly like lesson 05.
</details>

## Check yourself
1. Why train in one script and serve from another, instead of training inside the API?
2. Why is the model loaded at the top of `api.py`, not inside `predict()`?
3. What would happen if `predict()` passed the numbers in the order `[bedrooms, size, km]`?
4. Why validate the inputs with `Field(...)` when the model can compute a price for any numbers?

<details><summary>Answers</summary>

1. Training is slow and only needs to happen when the data changes. Serving must be fast and run all the time. Splitting them means the API starts instantly and you can retrain without changing the API code.
2. So it's loaded once when the server starts. Loading inside `predict()` would read the file on every request, making every answer slower.
3. The model would still answer, but wrongly: it would multiply the bedroom count by the "per m²" number and so on. The input order must match the training order exactly.
4. A model always produces a number, even for nonsense (like a negative price for a -5 m² house). Validation stops bad inputs at the door and tells the caller what's wrong.
</details>

## Learn more (optional)
- scikit-learn on saving models ("model persistence"): https://scikit-learn.org/stable/model_persistence.html
- FastAPI: body fields and validation: https://fastapi.tiangolo.com/tutorial/body-fields/
- Video: search YouTube for "deploy machine learning model FastAPI".

## Next
→ [Part 3 · Neural networks: 11 · One neuron learns](../../part-3-neural-networks/11-one-neuron-learns) (see the [Part 3 overview](../../part-3-neural-networks) for its install line)
