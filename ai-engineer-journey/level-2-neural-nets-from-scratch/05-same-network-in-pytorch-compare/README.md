# 2.5 · Same network in PyTorch: does your math match?

**What you'll build:** the XOR network from 2.3 twice, in NumPy (your hand-written gradients) and in PyTorch (automatic gradients), starting from **identical weights**. Then you check that the loss, the gradients and 3,000 training steps line up to many decimal places.
**Like you're 10:** you did your long division by hand, and now you check it on a calculator. Same answer means you truly understand what the calculator does.
**Time:** ~1 h · **Builds on:** [2.4 · Your own mini framework](../04-mini-framework-layer-classes) · **Needs:** PyTorch (CPU version is fine, no GPU needed)

## Why this matters
PyTorch is the framework most AI research and most production deep learning is written in, from image models to LLMs. From Level 4 on you'll use it every day. This project is the bridge: you see that `loss.backward()` computes exactly the numbers you computed by hand, so PyTorch becomes a fast, convenient version of something you already understand.

## What you'll learn
- **Tensor:** PyTorch's array (like a NumPy array, but it can track gradients and run on a GPU).
- **Autograd:** PyTorch records every operation on tensors and runs the chain rule backwards for you when you call `loss.backward()`.
- **`nn.Module` and `nn.Linear`:** PyTorch's layer classes (the grown-up version of your `Linear` from 2.4).
- **Optimizer:** `torch.optim.SGD` does `W -= lr * dW` for every parameter in `optimizer.step()`.
- **The 5-line training loop:** `zero_grad → forward → loss → backward → step`.

## Before you start
```bash
cd level-2-neural-nets-from-scratch/05-same-network-in-pytorch-compare
pip install -r requirements.txt
```
- `numpy`: your hand-written version.
- `torch`: PyTorch. The download is large (a few hundred MB). If you only want the CPU version (smaller, works everywhere), use the command from https://pytorch.org/get-started/locally/ (for Linux/Windows: `pip install torch --index-url https://download.pytorch.org/whl/cpu`).

No API key needed.

## Run it
```bash
python compare.py
```

### What you should see
```
loss      numpy 0.2774698018 | torch 0.2774698018
dW1 match: True
dW2 match: True
step    1 | numpy loss 0.277470 | torch loss 0.277470
step 1000 | numpy loss 0.002504 | torch loss 0.002504
step 3000 | numpy loss 0.000430 | torch loss 0.000430

Final predictions (numpy vs torch):
  [0 0]: 0.0129 vs 0.0129
  [0 1]: 0.9783 vs 0.9783
  [1 0]: 0.9799 vs 0.9799
  [1 1]: 0.0260 vs 0.0260

✅ Your hand-written backprop and PyTorch's autograd agree.
```
The first loss matches to 10 decimal places, both gradient checks say `True`, and after 3,000 steps the two versions are still identical. (Notice the starting loss `0.27747` is the same as in 2.3: same seed, same weights.)

## How it works
| Your NumPy code | PyTorch |
|-----------------|---------|
| `W1, b1` arrays, shape `(in, out)` | `torch.nn.Linear(2, 4)`: weight stored **transposed**, shape `(out, in)` |
| `sig(...)` | `torch.sigmoid(...)` |
| `np.mean((p - Y) ** 2)` | `torch.nn.MSELoss()` |
| `backward()` written by hand | `loss.backward()` |
| `W -= lr * dW` | `optimizer.step()` |
| gradients recomputed fresh each step | `optimizer.zero_grad()`, because PyTorch **adds** new gradients to old ones |

1. **Shared start:** `default_rng(42)` makes `W1_np`, `W2_np` exactly as in 2.3.
2. **Version A, `numpy_step()`:** one forward pass, the loss, the hand-written gradients from 2.3 (`dz2`, `dW2`, `dz1`, `dW1`...), and the updated weights. It returns all three so we can compare.
3. **Version B, `XorNet(torch.nn.Module)`:** `__init__` creates two `nn.Linear` layers (PyTorch makes the weights and biases for you, marked as trainable "parameters"); `forward(x)` is `sigmoid(out(sigmoid(hidden(x))))`. `.double()` switches to 64-bit floats like NumPy, so results match exactly rather than "nearly".
4. **Copying weights in:** inside `torch.no_grad()` (don't track this as part of the maths), `copy_` puts the NumPy weights into the layers. `W1_np.T` transposes them because `nn.Linear` stores weights as `(out, in)`.
5. **Comparing gradients:** `loss_t.backward()` fills `.grad` on every parameter. `np.allclose(grads_np[0], model.hidden.weight.grad.numpy().T)` checks they equal your `dW1` (to about 8 decimal places).
6. **Training both:** each step runs `numpy_step` and the PyTorch loop `optimizer.zero_grad()` → `model(X_t)` → `loss_fn(...)` → `loss_t.backward()` → `optimizer.step()`. The `zero_grad()` just before the loop clears the gradients left over from the comparison above.
7. **Final check:** `assert np.allclose(p_np, p_t, atol=1e-6)` fails loudly if the two versions ever drift apart.

## If something goes wrong
- **`ModuleNotFoundError: No module named 'torch'`** → `pip install -r requirements.txt` with your venv active. If pip says "no matching distribution", your Python is newer than the newest PyTorch build; check https://pytorch.org/get-started/locally/ for supported versions.
- **The install is slow or huge** → that's the CUDA (NVIDIA GPU) build. Use the CPU-only command from "Before you start".
- **`RuntimeError: mat1 and mat2 must have the same dtype`** → you removed `.double()` (model is float32, data is float64). Keep `.double()`, or make the data float32 with `torch.tensor(X_np, dtype=torch.float32)`.
- **`dW1 match: False`** after your edits → most likely a missing `.T`: PyTorch weights are `(out, in)`, NumPy ones are `(in, out)`.
- **`AssertionError` at the end** → the two versions drifted apart. Check that both use the same learning rate and that `zero_grad()` is still in the loop.

## Try this
1. Rewrite the PyTorch model with `torch.nn.Sequential` instead of the `XorNet` class. Do the results still match?
   <details><summary>Solution</summary>

   ```python
   model = torch.nn.Sequential(
       torch.nn.Linear(2, 4), torch.nn.Sigmoid(),
       torch.nn.Linear(4, 1), torch.nn.Sigmoid(),
   ).double()
   with torch.no_grad():
       model[0].weight.copy_(torch.tensor(W1_np.T)); model[0].bias.copy_(torch.tensor(b1_np))
       model[2].weight.copy_(torch.tensor(W2_np.T)); model[2].bias.copy_(torch.tensor(b2_np))
   ```
   Then use `model[0].weight.grad` and `model[2].weight.grad` in the two `match` lines. Everything still matches: `nn.Sequential` is PyTorch's version of your 2.4 `Sequential`.
   </details>
2. Delete the `optimizer.zero_grad()` line *inside* the training loop and run again. What happens, and why?
   <details><summary>Answer</summary>

   Step 1 still matches, but at step 1,000 PyTorch shows `torch loss 0.000000` while NumPy shows `0.002504`, and the final `assert` fails. Without `zero_grad()`, each `backward()` *adds* to the old gradients, so the step size keeps growing with the sum of all past gradients: a different (and usually broken) algorithm. Here it happens to race to zero, but on real problems it usually explodes. Always zero the gradients each step.
   </details>
3. Swap SGD for `torch.optim.Adam(model.parameters(), lr=0.05)` and count how many steps it takes to get the loss below 0.01.
   <details><summary>Solution</summary>

   Change the optimizer line, and in the loop add:
   ```python
   if loss_t.item() < 0.01:
       print("loss < 0.01 at step", step)
       break
   ```
   (Remove the final `assert`: NumPy is still doing plain SGD, so they won't match any more.) In our test, Adam got there at step 108; SGD with `lr = 2.0` needed 567 steps. Adam adapts the step size for each weight separately, which is why it's the default optimizer for most deep learning, including LLMs.
   </details>

## Check yourself
1. What does `loss.backward()` compute, and where does it put the results?
2. Why must we call `optimizer.zero_grad()` every step?
3. Why do we copy `W1_np.T` (transposed) into `model.hidden.weight`?
4. If PyTorch does backprop for you, why did you learn to do it by hand?

<details><summary>Answers</summary>

1. The gradient of the loss with respect to every parameter, using the chain rule over the recorded operations. It stores them in each parameter's `.grad`.
2. PyTorch adds new gradients to whatever is already in `.grad`. Without clearing, gradients from all previous steps pile up.
3. `nn.Linear` stores its weight as `(out_features, in_features)`, the transpose of our `(in, out)` NumPy layout.
4. So you can reason about it when things go wrong (vanishing gradients, `nan` losses, custom layers), and so it isn't magic: you now know exactly what those numbers are.
</details>

## Learn more (optional)
- PyTorch for Deep Learning, full course (Daniel Bourke): https://www.youtube.com/results?search_query=daniel+bourke+pytorch+for+deep+learning+full+course
- PyTorch "Learn the Basics" tutorial: https://pytorch.org/tutorials/beginner/basics/intro.html
- Have a GPU? Move the model and data with `.to("cuda")` (NVIDIA) or `.to("mps")` (Apple Silicon): https://pytorch.org/tutorials/beginner/basics/tensorqs_tutorial.html

## Next
→ [2.6 · Micrograd: build an autograd engine](../06-micrograd-autograd-engine)
