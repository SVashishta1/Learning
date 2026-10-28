"""Lesson 15: train GPT-2 with every trick of a real pretraining run (build-nanogpt style).

CPU, a few minutes (tiny model, Shakespeare, GPT-2 tokenizer):
    python train_gpt2.py
Start from OpenAI's real GPT-2 weights and fine-tune on Shakespeare (needs a GPU to be quick):
    python train_gpt2.py --preset gpt2 --init gpt2 --steps 200 --total-batch 16384 --micro-batch 8 --seq-len 512
The full GPT-2 (124M) reproduction on 10B tokens, 8 GPUs (see README "Cloud GPU recipe"):
    torchrun --standalone --nproc_per_node=8 train_gpt2.py --preset gpt2 --data fineweb_edu10B --steps 19073
"""
import argparse
import glob
import os
import time
import urllib.request

import numpy as np
import torch
import torch.distributed as dist
from torch.nn.parallel import DistributedDataParallel as DDP

from gpt2 import GPT, GPTConfig, cosine_lr

PRESETS = {
    #           model shape                              batch: tokens per optimizer step, per forward pass, sequence length
    "tiny": dict(n_layer=4, n_head=4, n_embd=128, total_batch=4096, micro_batch=4, seq_len=128,
                 max_lr=2e-3, warmup=20, steps=200, eval_every=50),
    "gpt2": dict(n_layer=12, n_head=12, n_embd=768, total_batch=524288, micro_batch=64, seq_len=1024,
                 max_lr=6e-4, warmup=715, steps=19073, eval_every=250),
}
p = argparse.ArgumentParser()
p.add_argument("--preset", choices=PRESETS, default="tiny")
p.add_argument("--init", choices=["scratch", "gpt2"], default="scratch", help="random weights or OpenAI's GPT-2")
p.add_argument("--data", default="shakespeare", help="'shakespeare' or a folder of token shards (*.bin from lesson 18 or *.npy)")
for name in ["steps", "total_batch", "micro_batch", "seq_len", "warmup", "eval_every"]:
    p.add_argument("--" + name.replace("_", "-"), type=int)
p.add_argument("--max-lr", type=float)
p.add_argument("--compile", action="store_true", help="torch.compile the model (GPU, PyTorch 2.x)")
args = p.parse_args()
H = dict(PRESETS[args.preset])
H.update({k: v for k, v in vars(args).items() if k in H and v is not None})

# ------------------------------------------------------------------ 1. who am I? (DDP = several GPUs)
# `torchrun` starts one copy of this script per GPU and sets RANK / LOCAL_RANK / WORLD_SIZE for each.
ddp = int(os.environ.get("RANK", -1)) != -1
if ddp:
    assert torch.cuda.is_available(), "DDP here needs CUDA GPUs"
    dist.init_process_group(backend="nccl")
    rank, local_rank, world = int(os.environ["RANK"]), int(os.environ["LOCAL_RANK"]), int(os.environ["WORLD_SIZE"])
    device = f"cuda:{local_rank}"
    torch.cuda.set_device(device)
else:
    rank, local_rank, world = 0, 0, 1
    device = "cuda" if torch.cuda.is_available() else "mps" if torch.backends.mps.is_available() else "cpu"
master = rank == 0                                       # only process 0 prints and saves
device_type = "cuda" if device.startswith("cuda") else device
torch.manual_seed(1337)
torch.set_float32_matmul_precision("high")               # allow TF32 on Ampere+ GPUs: ~3x faster matmuls
log = print if master else (lambda *a, **k: None)

# ------------------------------------------------------------------ 2. data
B, T = H["micro_batch"], H["seq_len"]
assert H["total_batch"] % (B * T * world) == 0, "total_batch must be divisible by micro_batch * seq_len * GPUs"
grad_accum = H["total_batch"] // (B * T * world)        # forward/backward passes per optimizer step


def load_shard(path):
    if path.endswith(".npy"):                            # build-nanogpt / fineweb.py format
        return torch.tensor(np.load(path).astype(np.int64))
    header = np.fromfile(path, dtype=np.int32, count=256)  # lesson 18 format: 256 int32 header, then uint16 tokens
    assert header[0] == 20240520, "unknown shard format"
    return torch.tensor(np.fromfile(path, dtype=np.uint16, offset=256 * 4)[: header[2]].astype(np.int64))


def shakespeare_tokens():
    import tiktoken
    if not os.path.exists("input.txt"):
        urllib.request.urlretrieve("https://raw.githubusercontent.com/karpathy/char-rnn/master/data/tinyshakespeare/input.txt", "input.txt")
    tokens = tiktoken.get_encoding("gpt2").encode(open("input.txt", encoding="utf-8").read())
    n = int(0.9 * len(tokens))
    return {"train": [torch.tensor(tokens[:n])], "val": [torch.tensor(tokens[n:])]}


class DataLoaderLite:
    """Walks through the token stream in order. Each GPU (rank) reads its own slice, so no two GPUs see the same data."""

    def __init__(self, shards):
        self.shards, self.shard = shards, 0     # tensors (Shakespeare) or file paths (big datasets: loaded one at a time)
        self.reset()

    def load(self, i):
        return load_shard(self.shards[i]) if isinstance(self.shards[i], str) else self.shards[i]

    def reset(self):
        self.shard = 0
        self.tokens = self.load(0)
        self.pos = B * T * rank

    def next_batch(self):
        buf = self.tokens[self.pos: self.pos + B * T + 1]
        x, y = buf[:-1].view(B, T), buf[1:].view(B, T)    # targets = inputs shifted by one token
        self.pos += B * T * world
        if self.pos + B * T * world + 1 > len(self.tokens):   # end of this shard: move to the next one
            self.shard = (self.shard + 1) % len(self.shards)
            self.tokens = self.load(self.shard)
            self.pos = B * T * rank
        return x.to(device), y.to(device)


if args.data == "shakespeare":
    splits = shakespeare_tokens()
else:
    splits = {s: sorted(glob.glob(os.path.join(args.data, f"*{s}*"))) for s in ("train", "val")}
    assert splits["train"] and splits["val"], f"no *train* / *val* shards found in {args.data}"
train_loader, val_loader = DataLoaderLite(splits["train"]), DataLoaderLite(splits["val"])
size = (f"train tokens {len(splits['train'][0]):,}" if args.data == "shakespeare" else f"train shards {len(splits['train'])}")
log(f"device {device} | GPUs {world} | tokens per step {H['total_batch']:,} = micro-batch {B} x seq {T} "
    f"x GPUs {world} x grad-accum {grad_accum} | {size}")

# ------------------------------------------------------------------ 3. model
if args.init == "gpt2":
    model = GPT.from_pretrained("gpt2")
else:
    # 50304 = 50257 rounded up to a multiple of 128: GPUs prefer "nice" numbers (the extra rows are never used)
    model = GPT(GPTConfig(vocab_size=50304, block_size=max(T, 128),
                          n_layer=H["n_layer"], n_head=H["n_head"], n_embd=H["n_embd"]))
model.to(device)
log(f"{sum(p.numel() for p in model.parameters()) / 1e6:.1f}M parameters ({'OpenAI GPT-2' if args.init == 'gpt2' else 'random init'})")
if args.compile:
    model = torch.compile(model)                         # turns Python into fused GPU kernels: fewer trips to memory
if ddp:
    model = DDP(model, device_ids=[local_rank])          # averages gradients across GPUs after each backward
raw_model = model.module if ddp else model
raw_model = getattr(raw_model, "_orig_mod", raw_model)   # unwrap torch.compile
optimizer = raw_model.configure_optimizers(weight_decay=0.1, learning_rate=H["max_lr"], device_type=device_type, verbose=master)
# bfloat16 autocast: matmuls in 16-bit on GPUs (2x less memory traffic), weights stay 32-bit.
use_amp = device_type == "cuda" and torch.cuda.is_bf16_supported()


def evaluate():
    model.eval()
    val_loader.reset()
    total = torch.zeros((), device=device)
    with torch.no_grad():
        for _ in range(10):
            x, y = val_loader.next_batch()
            with torch.autocast(device_type=device_type, dtype=torch.bfloat16, enabled=use_amp):
                total += model(x, y)[1] / 10
    if ddp:
        dist.all_reduce(total, op=dist.ReduceOp.AVG)
    model.train()
    return total.item()


# ------------------------------------------------------------------ 4. the training loop
for step in range(H["steps"] + 1):
    if step % H["eval_every"] == 0 or step == H["steps"]:
        log(f"step {step:5d} | val loss {evaluate():.4f}")
    if step == H["steps"]:
        break
    t0 = time.time()
    optimizer.zero_grad(set_to_none=True)
    loss_accum = 0.0
    for micro in range(grad_accum):                      # gradient accumulation: many small batches = one big batch
        x, y = train_loader.next_batch()
        with torch.autocast(device_type=device_type, dtype=torch.bfloat16, enabled=use_amp):
            _, loss = model(x, y)
        loss = loss / grad_accum                         # so the summed gradients equal the big batch's average
        loss_accum += loss.detach()
        if ddp:                                          # only talk to the other GPUs on the last micro-step
            model.require_backward_grad_sync = micro == grad_accum - 1
        loss.backward()                                  # gradients ADD UP in .grad until zero_grad
    if ddp:
        dist.all_reduce(loss_accum, op=dist.ReduceOp.AVG)
    norm = torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)   # cap the gradient's length at 1.0
    lr = cosine_lr(step, H["max_lr"], H["warmup"], H["steps"])
    for g in optimizer.param_groups:
        g["lr"] = lr
    optimizer.step()
    if device_type == "cuda":
        torch.cuda.synchronize()                         # wait for the GPU so the timing is honest
    dt = time.time() - t0
    if step % 10 == 0:
        log(f"step {step:5d} | loss {float(loss_accum):.4f} | lr {lr:.2e} | grad norm {float(norm):.2f} | "
            f"{dt * 1000:.0f} ms | {H['total_batch'] / dt:,.0f} tokens/s")

# ------------------------------------------------------------------ 5. save + sample
if master:
    torch.save({"model": raw_model.state_dict(), "config": raw_model.config.__dict__}, "gpt2_ckpt.pt")
    import tiktoken
    enc = tiktoken.get_encoding("gpt2")
    torch.manual_seed(42)
    start = torch.tensor([enc.encode("ROMEO:\n")], device=device)
    raw_model.eval()
    out = raw_model.generate(start, 60)[0].tolist()
    print("saved gpt2_ckpt.pt\n--- sample ---\n" + enc.decode([t for t in out if t < enc.n_vocab]))
if ddp:
    dist.destroy_process_group()
