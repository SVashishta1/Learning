"""Project 6.5 part B: run a small open LLM directly with transformers, no server needed.
Shows what a 'chat template' really looks like under the hood."""
import time

import torch
from transformers import AutoModelForCausalLM, AutoTokenizer

MODEL_ID = "HuggingFaceTB/SmolLM2-360M-Instruct"     # ~720 MB, runs on any laptop
tok = AutoTokenizer.from_pretrained(MODEL_ID)
model = AutoModelForCausalLM.from_pretrained(MODEL_ID)

messages = [{"role": "system", "content": "You are a concise assistant."},
            {"role": "user", "content": "Explain what a neural network is in two sentences."}]
prompt = tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)
print("=== What the model ACTUALLY sees (chat template) ===\n" + prompt)

ids = tok(prompt, return_tensors="pt")
start = time.time()
with torch.no_grad():
    out = model.generate(**ids, max_new_tokens=80, do_sample=True, temperature=0.7, top_p=0.9)
new_tokens = out[0][ids["input_ids"].shape[1]:]
print("=== Answer ===\n" + tok.decode(new_tokens, skip_special_tokens=True))
print(f"\n{len(new_tokens)} tokens in {time.time() - start:.1f}s = {len(new_tokens) / (time.time() - start):.1f} tokens/sec on your machine")
