# Step 4: race PyTorch vs ONNX Runtime vs ONNX Runtime int8 on the same sentences, and check they agree.
# Usage: python compare_speed.py [model-folder-or-id]   (use the same model you exported)
import sys
import time
from pathlib import Path

import numpy as np
import onnxruntime as ort
import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

MODEL_ID = sys.argv[1] if len(sys.argv) > 1 else "distilbert/distilbert-base-uncased-finetuned-sst-2-english"
RUNS = 50                                     # how many times each contestant classifies the sentence
for f in ["exported/model.onnx", "exported/model-int8.onnx"]:
    if not Path(f).exists():
        sys.exit(f"Can't find {f}. Run export_to_onnx.py and quantize.py first.")

tokenizer = AutoTokenizer.from_pretrained("exported")
model = AutoModelForSequenceClassification.from_pretrained(MODEL_ID).eval()
inputs = tokenizer(["The story was slow at first, but the ending made me smile."], return_tensors="np")
feed = {"input_ids": inputs["input_ids"].astype(np.int64),
        "attention_mask": inputs["attention_mask"].astype(np.int64)}


def pytorch_run():
    with torch.no_grad():                     # no_grad: we only predict, so skip the training bookkeeping
        return model(**{k: torch.from_numpy(v) for k, v in feed.items()}).logits.numpy()


def onnx_runner(path):
    def make():                               # the session is only created when it's this engine's turn
        session = ort.InferenceSession(path, providers=["CPUExecutionProvider"])
        return lambda: session.run(["logits"], feed)[0]
    return make


# Each entry makes its engine just before its turn. PyTorch goes first: onnxruntime's helper threads
# keep the CPU busy for a moment after they work, which would unfairly slow down whoever runs next.
contestants = {"PyTorch": lambda: pytorch_run,
               "ONNX Runtime": onnx_runner("exported/model.onnx"),
               "ONNX Runtime int8": onnx_runner("exported/model-int8.onnx")}

reference = pytorch_run()
print(f"{'engine':<18}{'ms per run':>11}{'same answer?':>14}{'max difference':>16}")
for name, make in contestants.items():
    run = make()
    for _ in range(3):                        # warm-up: the first runs are always slower
        run()
    start = time.perf_counter()
    for _ in range(RUNS):
        logits = run()
    ms = (time.perf_counter() - start) / RUNS * 1000
    same = logits.argmax() == reference.argmax()
    print(f"{name:<18}{ms:>11.2f}{'yes' if same else 'NO':>14}{np.abs(logits - reference).max():>16.4f}")
