"""Step 3: bake the LoRA patches into the model, so it becomes one normal Hugging Face model folder.

Run:  python merge.py
Makes: sprout-merged/   (~1 GB: config.json, model.safetensors, tokenizer files)
"""
import os

import torch
from peft import PeftModel
from transformers import AutoModelForCausalLM, AutoTokenizer

BASE = os.environ.get("BASE_MODEL", "Qwen/Qwen2.5-0.5B-Instruct")

model = AutoModelForCausalLM.from_pretrained(BASE, dtype=torch.float16)   # 16-bit is enough for exporting
model = PeftModel.from_pretrained(model, "sprout-lora")
model = model.merge_and_unload()            # W_new = W + (B x A) x alpha/r, then drop the separate patches
model.save_pretrained("sprout-merged")
AutoTokenizer.from_pretrained(BASE).save_pretrained("sprout-merged")
print("✅ Saved the merged model in sprout-merged/  (next: convert it to GGUF, see the README)")
