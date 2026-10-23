"""How much memory does a model need?

Weights:  parameters x bits per weight / 8      (the model's "knowledge")
KV cache: 2 x layers x kv_heads x head_dim x context x 2 bytes   (the model's "short-term memory")
Total:    (weights + KV cache) + 10% for the program's own buffers

Run:  python model_memory.py                 (the 4 Llama models, 8,192-token context)
      python model_memory.py --ctx 32768     (a longer conversation)
      python model_memory.py --params 14     (any model: 14 billion parameters, weights only)
"""
import argparse

GB = 1_000_000_000  # in this course 1 GB = 1 billion bytes

# How many bits it takes to store ONE weight in each file format.
# (Numbers from llama.cpp's `llama-quantize --help`: Q8_0 is 8.5 bits, Q4_K_M about 4.9 bits.)
FORMATS = {"FP16": 16.0, "Q8_0": 8.5, "Q4_K_M": 4.9}

# Real numbers from each model's config.json on Hugging Face.
MODELS = {
    "Llama 3.2 1B": dict(params=1.24e9, layers=16, kv_heads=8, head_dim=64),
    "Llama 3.2 3B": dict(params=3.21e9, layers=28, kv_heads=8, head_dim=128),
    "Llama 3.1 8B": dict(params=8.03e9, layers=32, kv_heads=8, head_dim=128),
    "Llama 3.1 70B": dict(params=70.6e9, layers=80, kv_heads=8, head_dim=128),
}

RAM_SIZES = [8, 16, 32, 64]  # common laptop / desktop memory sizes, in GB
USABLE = 0.75                # leave about a quarter of the RAM for your system and other apps
OVERHEAD = 1.10              # +10% for the program's working buffers


def weights_gb(params, bits):
    """Memory for the weights: every parameter takes `bits` bits, and 8 bits = 1 byte."""
    return params * bits / 8 / GB


def kv_cache_gb(layers, kv_heads, head_dim, ctx, bytes_per_value=2):
    """Memory for the KV cache. 2 = one Key and one Value vector, per layer, per token."""
    return 2 * layers * kv_heads * head_dim * ctx * bytes_per_value / GB


def fits(total):
    """Which RAM sizes can hold `total` GB, after leaving room for everything else?"""
    return "  ".join(f"{ram:>3}GB:{'yes' if total <= ram * USABLE else ' no'}" for ram in RAM_SIZES)


def show_model(name, params, layers=None, kv_heads=None, head_dim=None, ctx=8192):
    print(f"\n{name}  ({params / 1e9:.2f} billion parameters)")
    kv = 0.0
    if layers:
        kv = kv_cache_gb(layers, kv_heads, head_dim, ctx)
        print(f"  KV cache for {ctx:,} tokens: {kv:.2f} GB")
    else:
        print("  (no layer details given, so the KV cache is not included)")
    print(f"  {'format':<8}{'bits':>6}{'weights':>10}{'total':>9}   fits in (using 75% of RAM)")
    for fmt, bits in FORMATS.items():
        w = weights_gb(params, bits)
        total = (w + kv) * OVERHEAD
        print(f"  {fmt:<8}{bits:>6.1f}{w:>8.2f}GB{total:>7.2f}GB   {fits(total)}")


def main():
    parser = argparse.ArgumentParser(description="Estimate how much memory a local LLM needs.")
    parser.add_argument("--ctx", type=int, default=8192, help="context length in tokens (default 8192)")
    parser.add_argument("--params", type=float, help="your own model size, in billions of parameters")
    parser.add_argument("--layers", type=int, help="number of layers (from the model's config)")
    parser.add_argument("--kv-heads", type=int, help="number of key/value heads")
    parser.add_argument("--head-dim", type=int, help="size of each attention head")
    args = parser.parse_args()

    layer_info = [args.layers, args.kv_heads, args.head_dim]
    if any(layer_info) and not all(layer_info):
        parser.error("give all three of --layers, --kv-heads and --head-dim (or none of them)")
    if args.params:
        show_model("Your model", args.params * 1e9, args.layers, args.kv_heads, args.head_dim, args.ctx)
    else:
        for name, cfg in MODELS.items():
            show_model(name, ctx=args.ctx, **cfg)
    print("\nRule of thumb: Q4_K_M needs about 0.6 GB per billion parameters, plus the KV cache.")


if __name__ == "__main__":
    main()
