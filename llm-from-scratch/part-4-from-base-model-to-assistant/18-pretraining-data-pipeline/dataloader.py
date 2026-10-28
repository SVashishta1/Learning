"""Lesson 18: read the token shards written by pipeline.py and serve training batches.

python dataloader.py                 # statistics + one decoded batch
python dataloader.py --data data/shards --batch 4 --seq 64
"""
import argparse
import glob
import os

import numpy as np
import torch

MAGIC = 20240520


def open_shard(path):
    """Memory-map a shard: the OS reads pieces from disk only when we touch them, so even
    100 GB of shards would not have to fit in RAM."""
    header = np.fromfile(path, dtype=np.int32, count=256)
    assert header[0] == MAGIC, f"{path} is not a shard written by pipeline.py"
    return np.memmap(path, dtype=np.uint16, mode="r", offset=256 * 4, shape=(int(header[2]),))


class ShardLoader:
    """Random batches from all shards of one split: pick a shard (bigger shards more often), pick a window."""

    def __init__(self, folder, split, batch_size, seq_len, seed=0):
        self.paths = sorted(glob.glob(os.path.join(folder, f"*_{split}_*.bin")))
        assert self.paths, f"no {split} shards in {folder}: run pipeline.py first"
        self.shards = [open_shard(p) for p in self.paths]
        sizes = np.array([len(s) for s in self.shards], dtype=np.float64)
        self.weights = sizes / sizes.sum()
        self.B, self.T = batch_size, seq_len
        self.rng = np.random.default_rng(seed)

    def num_tokens(self):
        return sum(len(s) for s in self.shards)

    def next_batch(self):
        xs, ys = [], []
        for _ in range(self.B):
            shard = self.shards[self.rng.choice(len(self.shards), p=self.weights)]
            i = self.rng.integers(0, len(shard) - self.T - 1)
            window = torch.from_numpy(shard[i:i + self.T + 1].astype(np.int64))   # T+1 tokens
            xs.append(window[:-1])                                                 # inputs
            ys.append(window[1:])                                                  # targets: shifted by one
        return torch.stack(xs), torch.stack(ys)


if __name__ == "__main__":
    p = argparse.ArgumentParser()
    p.add_argument("--data", default="data/shards")
    p.add_argument("--batch", type=int, default=4)
    p.add_argument("--seq", type=int, default=32)
    args = p.parse_args()

    train = ShardLoader(args.data, "train", args.batch, args.seq)
    val = ShardLoader(args.data, "val", args.batch, args.seq)
    print(f"train: {len(train.paths)} shards, {train.num_tokens():,} tokens | val: {len(val.paths)} shards, {val.num_tokens():,} tokens")
    x, y = train.next_batch()
    print(f"one batch: x {tuple(x.shape)}, y {tuple(y.shape)}, dtype {x.dtype}")
    print("x[0][:12] =", x[0][:12].tolist())
    print("y[0][:12] =", y[0][:12].tolist(), " <- the same numbers moved one step left")
    enc = None
    try:
        import tiktoken
        enc = tiktoken.get_encoding("gpt2")
        for row in x:
            print("  |", enc.decode(row.tolist()).replace("\n", "\\n"))
    except Exception as e:                       # decoding is only for looking; batches work without it
        print("(install tiktoken to see the text:", type(e).__name__, ")")
    counts = np.bincount(np.concatenate([np.asarray(s) for s in train.shards]), minlength=50257)
    eot = 50256
    print(f"documents in train (count of <|endoftext|>): {counts[eot]:,}")
    top = np.argsort(counts)[::-1][:8]
    if enc is not None:
        print("most common tokens:", [(enc.decode([int(t)]), int(counts[t])) for t in top])
