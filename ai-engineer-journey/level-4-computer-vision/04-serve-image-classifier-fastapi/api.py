"""Project 4.4: serve the image classifier from 4.3 behind POST /predict (upload a photo, get a label)."""
import io
import os
import time
from contextlib import asynccontextmanager

import torch
from fastapi import FastAPI, File, HTTPException, Query, UploadFile
from PIL import Image, UnidentifiedImageError

from common import eval_transform, load_checkpoint

MODEL_PATH = os.getenv("MODEL_PATH", "transfer_model.pt")   # override with: MODEL_PATH=other.pt uvicorn api:app
MAX_BYTES = 5 * 1024 * 1024                                   # 5 MB upload limit
state = {}                                                    # filled at startup: the model and its class names


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Load ONCE at startup, not per request (loading takes ~1 s; inference takes ~50 ms)
    if os.path.exists(MODEL_PATH):
        state["model"], state["classes"] = load_checkpoint(MODEL_PATH)
    yield
    state.clear()


app = FastAPI(title="Image classifier API", lifespan=lifespan)


@app.get("/health")
def health():
    return {"status": "ok", "model_loaded": "model" in state, "classes": state.get("classes", [])}


@app.post("/predict")
async def predict(file: UploadFile = File(...), top_k: int = Query(3, ge=1, le=10)):
    if "model" not in state:
        raise HTTPException(503, f"No model at {MODEL_PATH}. Train one in project 4.3 and copy it here.")
    data = await file.read()
    if len(data) > MAX_BYTES:
        raise HTTPException(413, "Image too large (max 5 MB)")
    try:
        img = Image.open(io.BytesIO(data)).convert("RGB")
    except (UnidentifiedImageError, OSError):          # not an image at all, or a broken/truncated one
        raise HTTPException(400, "That file isn't an image")
    start = time.perf_counter()
    with torch.no_grad():
        probs = torch.softmax(state["model"](eval_transform(img).unsqueeze(0)), dim=1)[0]
    top = probs.argsort(descending=True)[:top_k]
    return {"label": state["classes"][top[0]],
            "top": [{"label": state["classes"][i], "probability": round(probs[i].item(), 4)} for i in top],
            "inference_ms": round((time.perf_counter() - start) * 1000, 1)}
