# 13 · Same brain in PyTorch

**What it does:** solves the same XOR puzzle as project 12, in about half the code. **PyTorch** does the blame maths for you.

## Run it
```bash
cd part-3-neural-networks/13-same-brain-in-pytorch
python pytorch_brain.py
```

## The idea in one sentence
Every PyTorch training loop is the same 4 lines (**guess & measure → zero_grad → backward → step**), whether the model has 20 knobs or 20 billion.

## Try this
1. Swap `torch.optim.SGD(..., lr=2.0)` for `torch.optim.Adam(brain.parameters(), lr=0.05)`. Does it learn in fewer rounds?
2. Delete the `nudger.zero_grad()` line. What goes wrong?
