"""Open a GGUF file and look inside: its settings (metadata) and its weights (tensors).

Run:  python inspect_gguf.py models/Llama-3.2-1B-Instruct-Q4_K_M.gguf
"""
import sys
from collections import Counter
from pathlib import Path

from gguf import GGUFReader  # the official GGUF reader, made by the llama.cpp team

if len(sys.argv) != 2:
    sys.exit("Usage: python inspect_gguf.py path/to/model.gguf")
path = Path(sys.argv[1])
if not path.exists():
    sys.exit(f"File not found: {path}")

reader = GGUFReader(path)  # reads the header; the weights stay on disk until needed


def value(key, default="?"):
    """Read one metadata value, e.g. 'general.architecture' -> 'llama'."""
    field = reader.fields.get(key)
    return field.contents() if field else default


arch = value("general.architecture")
print(f"File:          {path.name}  ({path.stat().st_size / 1e9:.2f} GB)")
print(f"Name:          {value('general.name')}")
print(f"Architecture:  {arch}")
print(f"Layers:        {value(f'{arch}.block_count')}")
print(f"Context length:{value(f'{arch}.context_length'):>8} tokens (the most it was trained for)")
print(f"Embedding size:{value(f'{arch}.embedding_length'):>8} numbers per token")
print(f"Vocabulary:    {len(value('tokenizer.ggml.tokens', []))} tokens")
print(f"Chat template: {'yes' if 'tokenizer.chat_template' in reader.fields else 'no'}")

# Count the weights and see which number formats they are stored in.
types = Counter(t.tensor_type.name for t in reader.tensors)
params = sum(int(t.n_elements) for t in reader.tensors)
print(f"\nTensors:       {len(reader.tensors)}  ({params / 1e9:.2f} billion numbers)")
print(f"Bits per weight (average): {path.stat().st_size * 8 / params:.2f}")
print("Stored as:     " + ", ".join(f"{name} x{count}" for name, count in types.most_common()))

print("\nFirst 5 tensors:")
for t in reader.tensors[:5]:
    shape = " x ".join(str(int(n)) for n in t.shape)
    print(f"  {t.name:<28} {t.tensor_type.name:<6} {shape}")

print("\nAll metadata keys (settings):")
for key in reader.fields:
    if not key.startswith("GGUF.") and not key.startswith("tokenizer.ggml."):  # skip the huge word lists
        print("  " + key)
