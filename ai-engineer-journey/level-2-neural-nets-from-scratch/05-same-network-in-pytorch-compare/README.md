# 2.5 · Same network in PyTorch: does your math match?

**What you build:** the XOR network from 2.3 twice, in NumPy (your hand-written gradients) and in PyTorch (automatic gradients), starting from **identical weights**. Then you check the loss, the gradients and 3,000 training steps line up to many decimal places.
**Like you're 10:** you did your long division by hand, and now you check it on a calculator. Same answer means you truly understand what the calculator does.

## Run it
```bash
cd level-2-neural-nets-from-scratch/05-same-network-in-pytorch-compare
pip install -r requirements.txt     # torch is ~200 MB (CPU version is fine)
python compare.py
```
You should see `dW1 match: True`, matching loss columns, and the final ✅.

## NumPy → PyTorch dictionary
| Your NumPy code | PyTorch |
|-----------------|---------|
| `W1, b1` arrays | `torch.nn.Linear(2, 4)` (weight stored as **(out, in)**) |
| `sig(...)` | `torch.sigmoid(...)` |
| `backward()` by hand | `loss.backward()` |
| `W -= lr * dW` | `optimizer.step()` |
| (gradients recomputed fresh) | `optimizer.zero_grad()`, because PyTorch **accumulates** gradients |

## Key ideas
- **Autograd** records every operation you do on tensors and replays them backwards with the chain rule. That's what you did by hand.
- The **training loop is always the same 5 lines:** `zero_grad → forward → loss → backward → step`. You'll write it hundreds of times.
- `.double()` makes PyTorch use 64-bit floats like NumPy, so results match exactly.

## Your turn
1. Swap `SGD` for `torch.optim.Adam(model.parameters(), lr=0.05)`. How many steps does XOR take now?
2. Move the model to a GPU if you have one: `model.to("cuda")` (or `"mps"` on Apple Silicon).
3. Remove `optimizer.zero_grad()` and see what goes wrong.

## Watch
- PyTorch for Deep Learning, full course (Daniel Bourke): https://www.youtube.com/results?search_query=daniel+bourke+pytorch+for+deep+learning+full+course
- PyTorch "Learn the Basics" tutorial: https://pytorch.org/tutorials/beginner/basics/intro.html
