# Step 2: use the ONNX file with onnxruntime. No PyTorch needed for this part.
# Usage: python run_onnx.py                       (uses exported/model.onnx)
#        python run_onnx.py exported/model-int8.onnx
import sys
from pathlib import Path

import numpy as np
import onnxruntime as ort
from tokenizers import Tokenizer             # the small, fast tokenizer library (no PyTorch inside)

MODEL_FILE = Path(sys.argv[1] if len(sys.argv) > 1 else "exported/model.onnx")
FOLDER = MODEL_FILE.parent
if not MODEL_FILE.exists():
    sys.exit(f"Can't find {MODEL_FILE}. Run 'python export_to_onnx.py' first.")

tokenizer = Tokenizer.from_file(str(FOLDER / "tokenizer.json"))
tokenizer.enable_padding()                   # short sentences get [PAD] tokens so all rows are equally long
labels = (FOLDER / "labels.txt").read_text().splitlines()

session = ort.InferenceSession(str(MODEL_FILE), providers=["CPUExecutionProvider"])
print("Inputs :", [(i.name, i.shape) for i in session.get_inputs()])
print("Outputs:", [(o.name, o.shape) for o in session.get_outputs()])


def classify(sentences):
    encoded = tokenizer.encode_batch(sentences)
    feed = {
        "input_ids": np.array([e.ids for e in encoded], dtype=np.int64),
        "attention_mask": np.array([e.attention_mask for e in encoded], dtype=np.int64),
    }
    logits = session.run(["logits"], feed)[0]                # one row of scores per sentence
    probs = np.exp(logits) / np.exp(logits).sum(axis=1, keepdims=True)   # softmax: scores -> percentages
    return [(labels[p.argmax()], p.max()) for p in probs]


sentences = ["I love this film, it was wonderful!",
             "What a boring, terrible movie.",
             "The pizza was okay, I guess."]
print()
for text, (label, confidence) in zip(sentences, classify(sentences)):
    print(f"{label:>8} {confidence:6.1%}  {text}")
