"""Show a picture to a vision model running in Ollama and ask about it.

Run:  python describe_image.py shapes.png
      python describe_image.py my_photo.jpg "How many people are in this photo?"
"""
import base64
import io
import json
import os
import sys
import time
from pathlib import Path

import httpx
from PIL import Image

OLLAMA = os.environ.get("OLLAMA_URL", "http://localhost:11434")
MODEL = os.environ.get("VISION_MODEL", "qwen2.5vl:3b")
MAX_SIDE = 1024          # bigger photos are shrunk to this many pixels on the longest side


def image_to_base64(path):
    """Open any image, shrink it if it's huge, and turn it into base64 text (the format the API wants)."""
    img = Image.open(path).convert("RGB")           # RGB: drop transparency so it can be saved as JPEG
    img.thumbnail((MAX_SIDE, MAX_SIDE))              # keeps the shape; does nothing to small images
    buffer = io.BytesIO()                            # a "file" that lives in memory
    img.save(buffer, format="JPEG", quality=90)
    return base64.b64encode(buffer.getvalue()).decode("ascii")


if len(sys.argv) < 2:
    sys.exit('Usage: python describe_image.py <image> ["your question"]')
path = Path(sys.argv[1])
if not path.exists():
    sys.exit(f"Can't find {path}. Run 'python make_samples.py' to make shapes.png and receipt.png.")
question = sys.argv[2] if len(sys.argv) > 2 else "Describe this image in 2-3 sentences."

message = {"role": "user", "content": question, "images": [image_to_base64(path)]}
print(f"🖼️  {path.name} → {MODEL}\n❓ {question}\n🤖 ", end="", flush=True)
start, tokens_per_s = time.time(), 0.0
try:
    with httpx.stream("POST", f"{OLLAMA}/api/chat", timeout=300,
                      json={"model": MODEL, "messages": [message], "stream": True}) as response:
        for line in response.iter_lines():                  # Ollama sends one small JSON object per line
            chunk = json.loads(line)
            if "error" in chunk:
                sys.exit(f"\nOllama says: {chunk['error']}. Did you run 'ollama pull {MODEL}'?")
            print(chunk["message"]["content"], end="", flush=True)
            if chunk.get("done"):
                tokens_per_s = chunk["eval_count"] / (chunk["eval_duration"] / 1e9)
except httpx.ConnectError:
    sys.exit(f"\nCan't reach Ollama at {OLLAMA}. Open the Ollama app (or run 'ollama serve') and try again.")
print(f"\n\n⏱  {time.time() - start:.1f} s in total, {tokens_per_s:.1f} tokens/s while writing")
