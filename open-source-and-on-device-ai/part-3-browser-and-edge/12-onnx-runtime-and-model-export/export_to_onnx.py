# Step 1: turn a PyTorch model from Hugging Face into one portable ONNX file.
# Usage: python export_to_onnx.py                (the default sentiment model, ~270 MB download once)
#        python export_to_onnx.py <model-folder-or-id>   (any other text-classification model)
import sys
from pathlib import Path

import torch
from transformers import AutoModelForSequenceClassification, AutoTokenizer

MODEL_ID = sys.argv[1] if len(sys.argv) > 1 else "distilbert/distilbert-base-uncased-finetuned-sst-2-english"
OUT = Path("exported")                       # everything we make goes into this folder
OUT.mkdir(exist_ok=True)

print(f"Loading {MODEL_ID} ...")
tokenizer = AutoTokenizer.from_pretrained(MODEL_ID)
model = AutoModelForSequenceClassification.from_pretrained(MODEL_ID)
model.eval()                                 # "exam mode": no training behaviour such as dropout

# The exporter runs the model once on an example and records every step it takes.
example = tokenizer(["I love this film"], return_tensors="pt")
batch = torch.export.Dim("batch")            # "this size can change": how many sentences at once
words = torch.export.Dim("sequence")         # ... and how many tokens each sentence has

torch.onnx.export(
    model,
    (example["input_ids"], example["attention_mask"]),       # the example inputs, in forward() order
    OUT / "model.onnx",
    input_names=["input_ids", "attention_mask"],            # names we will use with onnxruntime
    output_names=["logits"],
    dynamic_shapes=({0: batch, 1: words}, {0: batch, 1: words}),
    external_data=False,                     # keep the weights inside model.onnx (one file, fine under 2 GB)
)

tokenizer.save_pretrained(OUT)               # the ONNX file only knows numbers, so keep the tokenizer next to it
(OUT / "labels.txt").write_text("\n".join(model.config.id2label[i] for i in range(model.config.num_labels)))

size_mb = (OUT / "model.onnx").stat().st_size / 1e6
print(f"\n✅ Saved {OUT / 'model.onnx'} ({size_mb:.1f} MB) plus the tokenizer and labels.txt")
