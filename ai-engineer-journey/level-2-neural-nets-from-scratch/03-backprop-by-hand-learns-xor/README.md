# 2.3 · Backprop by hand: learn XOR

**What you'll build:** a 2 → 4 → 1 network that learns XOR. You write **every gradient yourself** with the chain rule, prove they're right with a gradient check, then train for 5,000 steps.
**Like you're 10:** a team lost a game. The coach (backprop) walks backwards from the final score: "the striker missed because the midfielder's pass was late, because the defender..." Everyone learns *their own* share of the blame and practises just that.
**Time:** ~2 h · **Builds on:** [2.2 · Forward pass](../02-forward-pass-two-layer-network-numpy) · **Needs:** nothing extra

## Why this matters
Backpropagation is the algorithm that trains every neural network in use today. PyTorch and TensorFlow run it for you, but when training goes wrong (loss stuck, `nan`, a custom layer misbehaving) engineers who understand it can find the problem. The gradient check you write here is the same tool researchers use to test new layers.

## What you'll learn
- **Chain rule:** if the loss depends on `p`, `p` on `z2`, and `z2` on `W2`, then `dLoss/dW2 = dLoss/dp × dp/dz2 × dz2/dW2`.
- **Backpropagation:** applying the chain rule from the loss back to the first layer, reusing each piece on the way.
- **Gradient check:** comparing your calculus with the "nudge" method from 2.1 to catch bugs.
- **Why XOR needs a hidden layer:** no single straight line separates XOR's 1s from its 0s; the hidden layer bends the space so one line works.
- **Training loop:** forward → loss → backward → update, thousands of times.

## Before you start
```bash
cd level-2-neural-nets-from-scratch/03-backprop-by-hand-learns-xor
pip install -r requirements.txt
```
- `numpy`: arrays and matrix maths.

No API key needed.

## Run it
```bash
python backprop_xor.py
```

### What you should see
```
gradient check W1[0,0]: by hand -0.000043 | nudge -0.000043
gradient check W1[0,1]: by hand -0.000099 | nudge -0.000099
gradient check W1[0,2]: by hand +0.007435 | nudge +0.007435
gradient check W1[0,3]: by hand +0.008027 | nudge +0.008027
gradient check W1[1,0]: by hand -0.000088 | nudge -0.000088
gradient check W1[1,1]: by hand +0.000898 | nudge +0.000898
gradient check W1[1,2]: by hand +0.004188 | nudge +0.004188
gradient check W1[1,3]: by hand +0.004957 | nudge +0.004957
biggest difference: 3.3e-11
epoch     1 | loss 0.27747
epoch   100 | loss 0.20407
epoch   500 | loss 0.01508
epoch  1000 | loss 0.00250
epoch  2500 | loss 0.00056
epoch  5000 | loss 0.00022

XOR learned:
  [0 0] -> 0.009  (want 0) ✅
  [0 1] -> 0.984  (want 1) ✅
  [1 0] -> 0.986  (want 1) ✅
  [1 1] -> 0.019  (want 0) ✅
```
First, all 8 hand-made gradients match the nudge method to about 11 decimal places, so backprop is correct. Then the loss falls from ~0.28 (guessing ~0.5 for everything) to ~0.0002, and all four XOR answers are right.

## How it works
```
FORWARD:   X ──@W1+b1──► z1 ──sigmoid──► h ──@W2+b2──► z2 ──sigmoid──► p ──► loss = mean((p - Y)^2)
BACKWARD:  dW1 ◄── dz1 ◄── dh ◄────────── dW2 ◄── dz2 ◄────────────── dp ◄──┘
           (each arrow multiplies by one local derivative: that's the chain rule)
```
1. **Data:** `X` holds the 4 input pairs, `Y` the XOR answers. `W1` is `(2, 4)`, `W2` is `(4, 1)`, biases start at zero, and `default_rng(42)` makes the random start the same every run.
2. **`forward()`** is 2.2's forward pass, but it returns every middle value (`z1, h, z2, p`), because backward needs them.
3. **`loss_fn()`** is mean squared error, as in 2.1.
4. **`backward()`** reads bottom-up from the loss, one chain-rule link per line:
   - `dp = 2 * (p - Y) / n`: how the loss changes with each prediction (derivative of the mean squared error).
   - `dz2 = dp * p * (1 - p)`: through the sigmoid, whose derivative is `s * (1 - s)`.
   - `dW2 = h.T @ dz2`: since `z2 = h @ W2`, each weight's blame is its input times the blame of the output. `db2` sums the blame over the 4 examples.
   - `dh = dz2 @ W2.T`: blame flows back to the hidden neurons through the same weights it came forward on.
   - `dz1`, `dW1`, `db1`: the same two steps again for the first layer.
5. **Gradient check:** for every weight in `W1`, nudge it up by `eps = 1e-6`, then down, and compute `(loss_up - loss_down) / (2 * eps)`: the slope measured from both sides (more accurate than one side). If any hand-made gradient differs by more than `1e-7`, the `assert` stops the program: "backprop has a bug!".
6. **Training loop:** 5,000 times: `forward`, `backward`, then `W -= lr * dW` for every weight and bias, with a big learning rate `lr = 2.0` (fine for this tiny problem).
7. **Result:** `round(pi)` turns each prediction into 0 or 1 and compares it with the answer.

## If something goes wrong
- **`AssertionError: backprop has a bug!`** → after your edits, a line in `backward()` is wrong. Check each shape (`print(dW1.shape, W1.shape)` must match) and each local derivative.
- **The loss stays around 0.25 or 0.17 and some answers are ❌** → training got stuck (for example, after changing the hidden size or the seed). Try another seed in `default_rng(...)`, more epochs, or a bigger hidden layer.
- **`ValueError: operands could not be broadcast together`** → a shape mismatch, often from forgetting `.T` (transpose) in `h.T @ dz2` or `dz2 @ W2.T`.
- **`ModuleNotFoundError: No module named 'matplotlib'`** (exercise 2) → `pip install matplotlib`.

## Try this
1. Add a gradient check for `W2` too.
   <details><summary>Solution</summary>

   Paste this just before the training loop:
   ```python
   _, _, dW2, _ = backward(X, Y, h, p, W2)
   for i, j in np.ndindex(W2.shape):
       W2_up, W2_down = W2.copy(), W2.copy()
       W2_up[i, j] += eps
       W2_down[i, j] -= eps
       numeric = (loss_fn(forward(X, W1, b1, W2_up, b2)[3], Y) - loss_fn(forward(X, W1, b1, W2_down, b2)[3], Y)) / (2 * eps)
       print(f"gradient check W2[{i},{j}]: by hand {dW2[i, j]:+.6f} | nudge {numeric:+.6f}")
       assert abs(dW2[i, j] - numeric) < 1e-7
   ```
   You'll see four matching lines like `W2[0,0]: by hand +0.025788 | nudge +0.025788`.
   </details>
2. Try `lr = 0.1` and `lr = 10`, and plot loss vs. epoch with matplotlib.
   <details><summary>Solution</summary>

   Collect the losses in the loop with `losses.append(loss_fn(p, Y))` (start with `losses = []`), then:
   ```python
   import matplotlib.pyplot as plt
   plt.plot(losses)
   plt.xlabel("epoch"); plt.ylabel("loss"); plt.yscale("log")
   plt.savefig("loss.png")
   ```
   In our runs, `lr = 0.1` is still stuck near 0.14 after 5,000 epochs (too slow, some answers wrong), `lr = 2.0` reaches 0.0002, and `lr = 10` reaches 0.00005. Big learning rates work here because the problem is tiny; on real data they usually explode.
   </details>
3. Change the hidden size from 4 to 2 (`(2, 2)` and `(2, 1)` for the weights, `np.zeros(2)` for `b1`). Does it still learn? Try seeds 0 to 5.
   <details><summary>Answer</summary>

   Usually yes: 2 hidden neurons is the minimum XOR needs. In our test, seeds 0 to 4 learned perfectly, but seed 5 got stuck with loss ≈ 0.17 and outputs like `[0.33, 0.98, 0.33, 0.33]`, and about 4 seeds out of 20 got stuck. With barely enough neurons, a bad start can trap training in a "local minimum". That's one reason real networks are made bigger than strictly necessary.
   </details>

## Check yourself
1. In your own words, what is the chain rule doing in `backward()`?
2. Why does `backward()` need `h` and `p` from the forward pass?
3. Why is a gradient check worth doing, and why don't we use the nudge method for training?
4. Why can't a single neuron (no hidden layer) learn XOR?

<details><summary>Answers</summary>

1. It passes blame backwards: each step multiplies the blame arriving from above by how much this step's output depends on its input, giving each weight its share of the error.
2. The local derivatives use them: the sigmoid's derivative is `p * (1 - p)`, and each weight's gradient is its input (`h` or `X`) times the blame of its output.
3. Hand-written gradients are easy to get subtly wrong; the nudge method is slow but obviously correct, so it catches bugs. It's too slow for training because it needs two extra loss calculations per weight per step.
4. A single neuron draws one straight line (a weighted sum, then a squash). XOR's 1s are on opposite corners of the square, so no straight line can separate them from the 0s.
</details>

## Learn more (optional)
- What is backpropagation really doing? (3Blue1Brown): https://www.youtube.com/results?search_query=3blue1brown+what+is+backpropagation+really+doing
- Backpropagation calculus (3Blue1Brown): https://www.youtube.com/results?search_query=3blue1brown+backpropagation+calculus
- CS231n notes on backprop: https://cs231n.github.io/optimization-2/

## Next
→ [2.4 · Your own mini framework (Layer classes)](../04-mini-framework-layer-classes)
