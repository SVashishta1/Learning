# 4.4 · Serve it: an image classifier behind `/predict`

**What you'll build:** a FastAPI service where anyone can upload a photo and get back a label, the top-3 probabilities, and how long the model took. It serves the model you trained in 4.3.
**Like you're 10:** your model was a genius living in your laptop's notebook. Now it gets a **front desk**: anyone can hand it a photo through the window and get an answer back.
**Time:** ~1.5 h · **Builds on:** [4.3 Transfer learning](../03-transfer-learning-resnet-on-your-own-photos) and [Level 1 APIs](../../level-1-apis) · **Needs:** a trained `transfer_model.pt` from 4.3 (the tests don't need it)

## Why this matters
A model in a notebook helps nobody. Companies put models behind an API so apps, websites and other services can use them. That's what "deploying a model" means in most ML engineering jobs. Doing it well means loading the model once, validating every upload, using the exact same preprocessing as training, and reporting health and speed. Those are the habits this project builds.

## What you'll learn
- **Load once, predict many**: load the model at server startup (slow), then answer each request quickly.
- **File uploads in FastAPI**: receiving a photo with `UploadFile`.
- **Validating untrusted input**: rejecting huge files (413) and non-images (400) before they reach the model.
- **Training/serving consistency**: sharing `common.py` so the API prepares images exactly as training did.
- **Health checks and latency**: `/health` for deploy platforms, `inference_ms` for dashboards.

## Before you start
```bash
pip install -r requirements.txt
```
- `torch`, `torchvision`, `pillow`: load the ResNet model and open/transform images.
- `fastapi`, `uvicorn[standard]`: the API and the server that runs it.
- `python-multipart`: lets FastAPI read file uploads (forms). Without it, the upload endpoint fails to start.
- `httpx`, `pytest`: run the tests.

No API key needed. To serve real predictions you need `transfer_model.pt` from 4.3. The tests build their own throwaway model, so they work without it.

## Run it
1. From the course root:
   ```bash
   cd level-4-computer-vision/04-serve-image-classifier-fastapi
   pip install -r requirements.txt
   ```
2. Copy your trained model from 4.3 into this folder:
   ```bash
   cp ../03-transfer-learning-resnet-on-your-own-photos/transfer_model.pt .
   ```
   (Windows Command Prompt: `copy ..\03-transfer-learning-resnet-on-your-own-photos\transfer_model.pt .`)
3. Start the server:
   ```bash
   uvicorn api:app --reload
   ```
4. Try it:
   - Browser: http://127.0.0.1:8000/docs → `POST /predict` → **Try it out** → **Choose File** → **Execute**.
   - Terminal (a second window, from a folder with a photo in it): `curl -F "file=@my_photo.jpg" http://127.0.0.1:8000/predict`
   - Health: http://127.0.0.1:8000/health
5. Stop the server with `Ctrl+C` and run the tests:
   ```bash
   pytest -v
   ```

### What you should see
These responses are real, from a test model trained in 4.3 on stand-in pictures (the real ResNet weights couldn't be downloaded where this lesson was checked). Your probabilities and timings will differ.

`GET /health`:
```json
{"status":"ok","model_loaded":true,"classes":["airplane","car","ship"]}
```
`curl -F "file=@my_photo.jpg" http://127.0.0.1:8000/predict`:
```json
{"label":"ship","top":[{"label":"ship","probability":0.7249},{"label":"airplane","probability":0.1807},{"label":"car","probability":0.0944}],"inference_ms":307.9}
```
Uploading a text file instead of a photo:
```json
{"detail":"That file isn't an image"}
```
Without `transfer_model.pt` in the folder, `/health` says `"model_loaded": false` and `/predict` returns `503` with `"No model at transfer_model.pt. Train one in project 4.3 and copy it here."`

`pytest -v` ends with `4 passed`.

What to look at:
- **`top` probabilities add up to 1** (softmax over your classes).
- **`inference_ms`** is just the model's thinking time. On a laptop CPU, ResNet-18 takes roughly 20–300 ms per photo depending on the machine. The first request is often slower (warm-up).

## How it works
```
client ──POST /predict (photo)──► FastAPI
                                    │ 1. model loaded? (no → 503)
                                    │ 2. read bytes, > 5 MB? (→ 413)
                                    │ 3. Pillow can open it? (no → 400)
                                    │ 4. eval_transform → model → softmax
                                    ▼
client ◄── {"label", "top", "inference_ms"} ──
```
1. **`common.py`** is an exact copy of 4.3's file. Serving must use the same `eval_transform` (resize 256 → crop 224 → normalise) and the same `build_model` shape as training, or predictions silently go wrong. Copying one shared file is the simplest way to guarantee that.
2. **Settings.** `MODEL_PATH` comes from an environment variable if set (that's how you point a deployed app at a different file, and how the tests use a throwaway model), otherwise `transfer_model.pt`. `MAX_BYTES` is the 5 MB upload limit.
3. **`lifespan()`** runs once when the server starts, before any request. It loads the model into the `state` dictionary with `load_checkpoint()` (which also switches it to `eval()` mode). Loading takes about a second; predicting takes milliseconds, so you never load inside a request. Code after `yield` runs on shutdown.
4. **`GET /health`** reports whether the model is loaded and which classes it knows. Deployment platforms call a URL like this to decide when your app is ready for traffic.
5. **`POST /predict`**:
   - `file: UploadFile = File(...)` receives the upload (this is what needs `python-multipart`). `top_k` is an optional query parameter (`/predict?top_k=2`), limited to 1–10 by `Query(3, ge=1, le=10)`.
   - It reads the bytes and rejects anything over 5 MB with **413 Payload Too Large**. Never trust user uploads.
   - `Image.open(...).convert("RGB")` checks it's really an image (and makes greyscale/transparent images 3-channel). If Pillow can't open it, the API answers **400 Bad Request** instead of crashing with a 500.
   - Inside `torch.no_grad()` it runs the model, applies `softmax` to get probabilities, sorts them with `argsort(descending=True)`, and returns the best label, the top-k list, and the time measured with `time.perf_counter()`.
6. **`test_api.py`** saves an *untrained* 3-class model to a temporary folder and points `MODEL_PATH` at it **before** importing `api` (because `api.py` reads the variable on import). `with TestClient(app) as client:` runs the startup code, then the tests check `/health`, a valid prediction (label is one of the classes, probabilities sum to 1), a text file (400), and a 5 MB+ upload (413). No real model or server needed.

## If something goes wrong
- **`503: No model at transfer_model.pt`** → copy `transfer_model.pt` from 4.3 into this folder (step 2), then restart uvicorn (the model is loaded at startup).
- **`RuntimeError: Form data requires "python-multipart" to be installed`** → `pip install python-multipart` (it's in `requirements.txt`).
- **`RuntimeError: Error(s) in loading state_dict ... size mismatch for fc.weight`** → the checkpoint was made with a different model shape (e.g. you changed `build_model` in 4.3, like MobileNet in its "Try this"). Copy the same `common.py` from 4.3 into this folder.
- **`[Errno 48/98] Address already in use`** → another server is on port 8000. Stop it or use `uvicorn api:app --reload --port 8001`.
- **`curl: (26) Failed to open/read local file data`** → the `@` path is wrong. Run curl from the folder that contains the photo, or give the full path: `-F "file=@/full/path/photo.jpg"`.

## Try this
1. **Batch endpoint.** Add `POST /predict/batch` that accepts several files at once and returns a list of results.
   <details><summary>Solution</summary>

   Add to `api.py`:
   ```python
   @app.post("/predict/batch")
   async def predict_batch(files: list[UploadFile] = File(...)):
       return [await predict(f, top_k=3) for f in files]
   ```
   In `/docs` you can now add several files. With curl: `curl -F "files=@a.jpg" -F "files=@b.jpg" http://127.0.0.1:8000/predict/batch`. (We pass `top_k=3` explicitly because we're calling the function directly, not through FastAPI.)
   </details>
2. **Model monitoring.** Log every prediction (time, label, probability, latency) to a SQLite table, as in 1.5, and add `GET /stats` that summarises it.
   <details><summary>Solution</summary>

   Near the top of `api.py`:
   ```python
   import sqlite3
   db = sqlite3.connect("predictions.db", check_same_thread=False)
   db.execute("CREATE TABLE IF NOT EXISTS predictions "
              "(ts TEXT DEFAULT CURRENT_TIMESTAMP, label TEXT, probability REAL, inference_ms REAL)")
   ```
   In `predict()`, save the dictionary in a variable `result` instead of returning it straight away, then:
   ```python
   db.execute("INSERT INTO predictions (label, probability, inference_ms) VALUES (?, ?, ?)",
              (result["label"], result["top"][0]["probability"], result["inference_ms"]))
   db.commit()
   return result
   ```
   And a summary endpoint:
   ```python
   @app.get("/stats")
   def stats():
       rows = db.execute("SELECT label, COUNT(*), ROUND(AVG(inference_ms), 1) FROM predictions GROUP BY label").fetchall()
       return [{"label": l, "count": n, "avg_ms": ms} for l, n, ms in rows]
   ```
   If one label suddenly dominates or average confidence drops, your users' photos have changed: that's the signal to retrain.
   </details>
3. **Dockerise it.** Package the API with the Dockerfile pattern from [1.7](../../level-1-apis/07-dockerize-and-deploy-to-the-cloud), using the CPU-only PyTorch build to keep the image small.
   <details><summary>Hint</summary>

   ```dockerfile
   FROM python:3.12-slim
   WORKDIR /app
   RUN pip install --no-cache-dir torch torchvision --index-url https://download.pytorch.org/whl/cpu
   COPY requirements.txt .
   RUN pip install --no-cache-dir -r requirements.txt
   COPY api.py common.py transfer_model.pt ./
   CMD ["uvicorn", "api:app", "--host", "0.0.0.0", "--port", "8000"]
   ```
   Installing the CPU wheels first means the second `pip install` sees torch is already there. The image is about 1 GB instead of 5+ GB with the GPU build.
   </details>

## Check yourself
1. Why is the model loaded in `lifespan()` instead of inside `predict()`?
2. Why do we check the file size and whether Pillow can open the file, instead of just passing it to the model?
3. What would go wrong if the API used `Resize(224)` without the same normalisation as training?
4. Why does the test set `MODEL_PATH` *before* `from api import app`?

<details><summary>Answers</summary>

1. Loading takes about a second and lots of memory; doing it per request would make every request slow. Load once, reuse for every prediction.
2. Uploads come from strangers. A huge file could exhaust memory, and a non-image would crash the model code with an unhelpful 500 error. Clear 413/400 errors protect the server and tell the user what's wrong.
3. The model would receive numbers in a different range and layout from what it learned on, so predictions would be much worse, without any error message. That's training/serving skew.
4. `api.py` reads `MODEL_PATH` once, at import time. If the variable were set afterwards, the API would already be looking for `transfer_model.pt`.
</details>

## Learn more (optional)
- FastAPI file uploads: https://fastapi.tiangolo.com/tutorial/request-files/
- FastAPI lifespan events: https://fastapi.tiangolo.com/advanced/events/
- Deploying ML models (Made With ML, free course): https://madewithml.com/

## Next
→ [4.5 · Draw-a-digit web app](../05-draw-a-digit-web-app)
