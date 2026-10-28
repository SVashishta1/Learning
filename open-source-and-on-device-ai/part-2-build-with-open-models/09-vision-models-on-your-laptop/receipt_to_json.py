"""Read a photo of a receipt into clean JSON, checked by Pydantic, then double-check the maths.

Run:  python receipt_to_json.py receipt.png
Makes: receipt.json
"""
import base64
import io
import json
import os
import sys
from pathlib import Path

import httpx
from PIL import Image
from pydantic import BaseModel, Field, ValidationError

OLLAMA = os.environ.get("OLLAMA_URL", "http://localhost:11434")
MODEL = os.environ.get("VISION_MODEL", "qwen2.5vl:3b")


# The shape we want back. Pydantic turns this into a JSON schema that Ollama forces the model to follow.
class Item(BaseModel):
    name: str
    quantity: int = Field(ge=1)                     # ge=1: "greater than or equal to 1"
    price: float = Field(description="line total for this item, not the unit price")


class Receipt(BaseModel):
    store: str
    date: str = Field(description="the purchase date as YYYY-MM-DD")
    items: list[Item]
    total: float
    currency: str = Field(description="3-letter code such as EUR, USD, GBP, INR")


def image_to_base64(path, max_side=1536):           # receipts need more pixels than photos: small print
    img = Image.open(path).convert("RGB")
    img.thumbnail((max_side, max_side))
    buffer = io.BytesIO()
    img.save(buffer, format="JPEG", quality=95)
    return base64.b64encode(buffer.getvalue()).decode("ascii")


if len(sys.argv) < 2:
    sys.exit("Usage: python receipt_to_json.py <receipt image>")
path = Path(sys.argv[1])
if not path.exists():
    sys.exit(f"Can't find {path}. Run 'python make_samples.py' to make receipt.png.")

prompt = ("Read this receipt. Return the store name, the date, every purchased item with its quantity "
          "and line price, the total and the currency. Copy numbers exactly as printed. "
          "If something is not printed, use an empty string.")
request = {
    "model": MODEL,
    "messages": [{"role": "user", "content": prompt, "images": [image_to_base64(path)]}],
    "format": Receipt.model_json_schema(),           # structured output: only JSON of this shape is allowed
    "options": {"temperature": 0},                   # 0 = always pick the most likely word: no creativity
    "stream": False,
}
print(f"🧾 Reading {path.name} with {MODEL} (this can take 10-60 s on a laptop)...")
try:
    data = httpx.post(f"{OLLAMA}/api/chat", json=request, timeout=300).json()
except httpx.ConnectError:
    sys.exit(f"Can't reach Ollama at {OLLAMA}. Open the Ollama app (or run 'ollama serve') and try again.")
if "error" in data:
    sys.exit(f"Ollama says: {data['error']}. Did you run 'ollama pull {MODEL}'?")

try:
    receipt = Receipt.model_validate_json(data["message"]["content"])    # check every field and type
except ValidationError as error:
    sys.exit(f"The model's answer didn't match the schema:\n{error}")

print(json.dumps(receipt.model_dump(), indent=2, ensure_ascii=False))
Path("receipt.json").write_text(receipt.model_dump_json(indent=2))

# Never trust numbers read by a model without a check: do the items add up to the total?
items_sum = round(sum(item.price for item in receipt.items), 2)
if abs(items_sum - receipt.total) < 0.01:
    print(f"\n✅ Items add up to the total ({items_sum:.2f} {receipt.currency}). Saved receipt.json")
else:
    print(f"\n⚠️  Items add up to {items_sum:.2f} but the total says {receipt.total:.2f}: "
          "check this receipt by hand. Saved receipt.json anyway.")
