# 4.4 · Serve it: an image classifier behind `/predict`

**What you build:** a FastAPI service where you upload a photo and get back a label, the top-3 probabilities, and how long inference took. It serves the model you trained in 4.3.
**Like you're 10:** your model was a genius living in your laptop's notebook. Now it gets a **front desk**: anyone can hand it a photo through the window and get an answer back.

## Run it
```bash
cd level-4-computer-vision/04-serve-image-classifier-fastapi
pip install -r requirements.txt
cp ../03-transfer-learning-resnet-on-your-own-photos/transfer_model.pt .
uvicorn api:app --reload
```
- http://127.0.0.1:8000/docs → `POST /predict` → **Choose File** → Execute
- Or: `curl -F "file=@my_photo.jpg" localhost:8000/predict`

Test (no trained model needed): `pytest -v`

## Key ideas
- **Load once, predict many:** the model loads at startup, never inside the request.
- **Validate uploads:** check size (413) and that the file is really an image (400). Never trust user files.
- **Same preprocessing as training:** `common.py` is shared so the API resizes and normalises *exactly* like training did.
- **Latency:** `inference_ms` is the number you'd watch on a production dashboard.
- **Health check** reports whether the model is loaded, so a deploy platform can wait until it's ready.

## Your turn
1. Add `POST /predict/batch` accepting several files.
2. Log every prediction (label, probability, latency) to a SQLite table, as in 1.5. Congratulations, you've built **model monitoring**.
3. Dockerize it (Dockerfile pattern from 1.7). Use the CPU-only torch wheel to keep the image small.

## Watch
- FastAPI file uploads: https://fastapi.tiangolo.com/tutorial/request-files/
- Deploying ML models (Made With ML, free course): https://madewithml.com/
