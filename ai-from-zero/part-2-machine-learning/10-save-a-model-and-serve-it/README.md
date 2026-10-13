# 10 · Save a model and serve it as an API

**What it does:** trains the house-price model once, saves it to a file, and lets anyone get a price estimate through a web API. This is how ML models are used in real apps.

## Run it
```bash
cd part-2-machine-learning/10-save-a-model-and-serve-it
python train.py
uvicorn api:app --reload
```
Open http://127.0.0.1:8000/docs → **POST /predict** → Try it out → send:
```json
{"size_m2": 120, "bedrooms": 3, "km_to_centre": 5}
```

## The idea in one sentence
Training is slow and happens once; the saved model file is then loaded by an API that answers predictions in milliseconds.

## Try this
1. Send `"size_m2": -5`. The API refuses with a clear error, so bad data never reaches the model.
2. Deploy it with the Dockerfile pattern from project 05 (copy `house_model.joblib` into the image too).
