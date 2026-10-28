"""What fits where? Which models can run on a Raspberry Pi, a phone, a Mac... and roughly how fast.

Memory  = (weights + KV cache) x 1.10           (the same maths as lesson 01)
Speed  ~= memory bandwidth x 50% / model size   (to write ONE token, the chip reads ALL the weights once)

Run:  python what_fits.py                    (every device, 4,096-token context)
      python what_fits.py --device "Pi 5 8GB"
      python what_fits.py --ram 6 --bandwidth 25    (your own device: 6 GB RAM, 25 GB/s)
"""
import argparse

GB = 1_000_000_000
BITS = {"Q4_K_M": 4.9, "Q8_0": 8.5}          # bits per weight (llama-quantize --help)
OVERHEAD = 1.10                               # +10% for the program's working buffers
EFFICIENCY = 0.5                              # real programs reach about half the chip's top bandwidth

# name: (parameters, layers, kv_heads, head_dim)  from each model's config.json
MODELS = {
    "Qwen2.5 0.5B": (0.49e9, 24, 2, 64),
    "Llama 3.2 1B": (1.24e9, 16, 8, 64),
    "Qwen2.5 1.5B": (1.54e9, 28, 2, 128),
    "Llama 3.2 3B": (3.21e9, 28, 8, 128),
    "Llama 3.1 8B": (8.03e9, 32, 8, 128),
}

# name: (total RAM in GB, share of RAM one app can really use, memory bandwidth in GB/s)
# Phones keep a lot of RAM for the system and other apps, so an app gets less than half.
DEVICES = {
    "Pi 5 4GB": (4, 0.70, 17),
    "Pi 5 8GB": (8, 0.75, 17),
    "Pi 5 16GB": (16, 0.80, 17),
    "Jetson Orin Nano 8GB": (8, 0.70, 68),
    "Phone 8GB (Android/iPhone)": (8, 0.45, 60),
    "Phone 12GB (Android)": (12, 0.50, 77),
    "Mac M-chip 16GB": (16, 0.70, 120),
    "Laptop 16GB (CPU only)": (16, 0.70, 60),
}


def model_gb(params, layers, kv_heads, head_dim, quant, ctx):
    weights = params * BITS[quant] / 8
    kv_cache = 2 * layers * kv_heads * head_dim * ctx * 2      # Keys + Values, 2 bytes each
    return (weights + kv_cache) * OVERHEAD / GB, weights / GB


def show(device, ram, usable, bandwidth, ctx):
    budget = ram * usable
    print(f"\n📱 {device}: {ram} GB RAM, about {budget:.1f} GB usable by one app, {bandwidth} GB/s")
    print(f"   {'model':<14}{'quant':<8}{'needs':>8}   {'fits?':<7}{'speed guess':>12}")
    for name, (params, layers, kv_heads, head_dim) in MODELS.items():
        for quant in BITS:
            need, weights = model_gb(params, layers, kv_heads, head_dim, quant, ctx)
            if need <= budget * 0.8:
                verdict = "✅ yes"
            elif need <= budget:
                verdict = "⚠️ tight"
            else:
                verdict = "❌ no"
            speed = bandwidth * EFFICIENCY / weights                # tokens per second, rough
            speed_text = f"~{speed:.0f} tok/s" if need <= budget else "-"
            print(f"   {name:<14}{quant:<8}{need:>6.2f}GB   {verdict:<7}{speed_text:>12}")


def main():
    parser = argparse.ArgumentParser(description="Which local LLMs fit on which device?")
    parser.add_argument("--device", help="one device from the list, e.g. \"Pi 5 8GB\"")
    parser.add_argument("--ram", type=float, help="your own device's RAM in GB")
    parser.add_argument("--bandwidth", type=float, default=20, help="its memory bandwidth in GB/s (default 20)")
    parser.add_argument("--ctx", type=int, default=4096, help="context length in tokens (default 4096)")
    args = parser.parse_args()

    if args.ram:
        show("Your device", args.ram, 0.6, args.bandwidth, args.ctx)
    elif args.device:
        if args.device not in DEVICES:
            parser.error(f"unknown device. Choose one of: {', '.join(DEVICES)}")
        show(args.device, *DEVICES[args.device], args.ctx)
    else:
        for device, specs in DEVICES.items():
            show(device, *specs, args.ctx)
    print("\nSpeed guesses are for writing the answer (one token after another), on the CPU or GPU named.\n"
          "Reading your prompt is faster. Measure the real thing with speed_check.py or llama-bench.")


if __name__ == "__main__":
    main()
