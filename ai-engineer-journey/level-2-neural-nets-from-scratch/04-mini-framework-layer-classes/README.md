# 2.4 · Your own mini framework (Layer classes)

**What you'll build:** `tinyframe.py`, a mini PyTorch with `Linear`, `ReLU`, `Tanh`, `Sigmoid`, `Sequential`, an SGD step and a cross-entropy loss. Then you train it on XOR and on a curvy "two moons" dataset, and draw the boundary it learned (as text art and as `moons_boundary.png`).
**Like you're 10:** in 2.3 you built a car by welding every part by hand. Now you make **LEGO bricks** (layers) that snap together. Each brick knows two tricks: pass the ball forward, and pass the blame backward.
**Time:** ~2 h · **Builds on:** [2.3 · Backprop by hand](../03-backprop-by-hand-learns-xor) · **Needs:** nothing extra

## Why this matters
Writing every gradient by hand (2.3) doesn't scale past a couple of layers. Real frameworks (PyTorch, TensorFlow, JAX) solve this with exactly the design you build here: every layer knows its own forward and backward, and a container chains them. After this, `torch.nn.Linear`, `nn.Sequential` and `optimizer.step()` will look familiar instead of magic, and you'll be able to read framework source code.

## What you'll learn
- **Layer = forward + backward:** each layer computes its output, and later turns "blame for my output" into "blame for my input" (plus gradients for its own weights).
- **Sequential:** runs layers in order going forward, and in reverse order going backward.
- **Optimizer step:** a separate phase that nudges every parameter after all gradients are computed (here plain SGD).
- **Binary cross-entropy loss:** the standard loss for yes/no problems; it punishes confident wrong answers hard.
- **Weight initialisation:** scaling the random starting weights by layer size (Xavier/Glorot) keeps signals healthy.

## Before you start
```bash
cd level-2-neural-nets-from-scratch/04-mini-framework-layer-classes
pip install -r requirements.txt
```
- `numpy`: arrays and matrix maths.
- `matplotlib`: draws `moons_boundary.png` (optional: without it the script still runs and prints the text-art map).

No API key needed.

## Run it
```bash
python train_moons.py
```
It takes a few seconds and creates `moons_boundary.png` in this folder. Open it in VS Code or your image viewer.

### What you should see
```
[xor] epoch   400 | loss 0.0131 | accuracy 100%
[xor] epoch   800 | loss 0.0048 | accuracy 100%
[xor] epoch  1200 | loss 0.0028 | accuracy 100%
[xor] epoch  1600 | loss 0.0020 | accuracy 100%
[xor] epoch  2000 | loss 0.0015 | accuracy 100%
[moons] epoch   600 | loss 0.0068 | accuracy 100%
[moons] epoch  1200 | loss 0.0021 | accuracy 100%
[moons] epoch  1800 | loss 0.0011 | accuracy 100%
[moons] epoch  2400 | loss 0.0007 | accuracy 100%
[moons] epoch  3000 | loss 0.0005 | accuracy 100%

What the network thinks (A = class 0, B = class 1):
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAB
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABBB
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABBBBB
AAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABBBBBBB
AAAAAAAAAAAAAAAAAAAAABBBAAAAAAAAAAAAAAAAAAAAAAAAAAABBBBBBBBB
AAAAAAAAAAAAAAAAAABBBBBBBBBAAAAAAAAAAAAAAAAAAAAAABBBBBBBBBBB
AAAAAAAAAAAAAAABBBBBBBBBBBBBBAAAAAAAAAAAAAAAAABBBBBBBBBBBBBB
AAAAAAAAAAAAABBBBBBBBBBBBBBBBBBAAAAAAAAAAAAABBBBBBBBBBBBBBBB
AAAAAAAAAAABBBBBBBBBBBBBBBBBBBBBBBAAAAAAAABBBBBBBBBBBBBBBBBB
AAAAAAAAABBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB
AAAAAAABBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB
AAAAABBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB
AAABBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB
ABBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBBB

Saved moons_boundary.png
```
Accuracy reaches 100% on both datasets. In the map, look for the bump of **B**s pushing up into the **A**s left of the middle: that's the left tip of the lower moon poking up inside the upper moon's arch, and the network bent its boundary around it. `moons_boundary.png` shows the same thing in colour: red for class 0, blue for class 1, with a zig-zag boundary threading between the two moons. A straight line could never do that.

## How it works
```
Sequential(Linear, ReLU, Linear, ReLU, Linear, Sigmoid)
  forward:   X ─► Linear ─► ReLU ─► Linear ─► ReLU ─► Linear ─► Sigmoid ─► p ─► bce_loss
  backward:  grads ◄─ Linear ◄─ ReLU ◄─ Linear ◄─ ReLU ◄─ Linear ◄─ Sigmoid ◄─ dloss/dp
  step:      every Linear does W -= lr * dW,  b -= lr * db
```
**`tinyframe.py`**
1. **`Layer`** is the base class: every layer has `forward(x)` and `backward(grad)`, and a `params` list (empty for layers without weights).
2. **`Linear(n_in, n_out, rng)`** holds `W` (shape `(n_in, n_out)`) and `b`. Starting weights are random with spread `sqrt(2 / (n_in + n_out))` (**Xavier/Glorot** initialisation), so signals neither explode nor fade as they pass through layers. `forward` remembers its input `self.x` (backward needs it) and returns `x @ W + b`. `backward(grad)` stores `self.grads = [x.T @ grad, grad.sum(axis=0)]` (dW and db, exactly 2.3's formulas) and returns `grad @ W.T`, the blame for the layer before.
3. **`ReLU`** remembers `self.mask = x > 0`; backward lets gradient through only where the neuron was "on". **`Tanh`** and **`Sigmoid`** remember their output, because their derivatives (`1 - out²` and `out * (1 - out)`) are written in terms of it.
4. **`Sequential`** stores the layers. Calling it (`model(X)`) runs each `forward` in order; `backward` walks `reversed(self.layers)`, handing each layer's returned gradient to the one before; `step(lr)` subtracts `lr * grad` from every parameter **in place** (`p -= ...` changes the same array the layer uses).
5. **`bce_loss(p, y)`** returns the loss and its gradient. `np.clip` keeps `p` away from exactly 0 or 1, where `log` would blow up. Binary cross-entropy is `-mean(y*log(p) + (1-y)*log(1-p))`: predicting 0.01 when the answer is 1 costs a lot more than with squared error.

**`train_moons.py`**
6. **`train()`** is the universal loop: `p = model(X)` → `loss, grad = bce_loss(p, y)` → `model.backward(grad)` → `model.step(lr)`, printing loss and accuracy 5 times.
7. **XOR** with `Linear(2, 8) → Tanh → Linear(8, 1) → Sigmoid`: the whole of 2.3 in one line.
8. **Two moons:** 100 points along a half circle, 100 along a flipped, shifted half circle, plus noise. Network: 2 → 16 → 16 → 1 with ReLU.
9. **Drawing:** the text map asks the network about a grid of points and prints A or B; the matplotlib part colours a 200×200 grid by the predicted probability (`contourf`), draws the data on top, and saves the PNG.

## If something goes wrong
- **`ModuleNotFoundError: No module named 'tinyframe'`** → run the script from this folder (`train_moons.py` imports `tinyframe.py` next to it).
- **No PNG appears** → matplotlib isn't installed (the script silently skips the picture). Run `pip install -r requirements.txt`.
- **Loss becomes `nan` after your changes** → the learning rate is too big, or a backward method returns the wrong thing. Lower `lr` 10x and check each `backward` returns a gradient with the same shape as that layer's input.
- **`ValueError: operands could not be broadcast together`** in `backward` → a layer returned the gradient for its *weights* instead of its *input*, or the shapes of `y` and `p` differ (`y` must be shape `(n, 1)`, hence `.reshape(-1, 1)`).

## Try this
1. Shrink the moons network to `Linear(2, 4, rng), Tanh(), Linear(4, 1, rng), Sigmoid()`. Does it still reach 100%? Then remove the hidden layer entirely: `Linear(2, 1, rng), Sigmoid()`.
   <details><summary>Answer</summary>

   4 tanh neurons are enough: in our test it got stuck around 88% for a while, then reached 100% by epoch ~2,400. With no hidden layer it's just a straight line and stays at about 88% forever (loss ≈ 0.27): the moons interlock, so a line always misclassifies the tips.
   </details>
2. Add a `Dropout(p)` layer: during training, randomly zero a fraction `p` of the values (and scale the rest up so the average stays the same); when evaluating, do nothing.
   <details><summary>Solution</summary>

   ```python
   class Dropout(Layer):
       def __init__(self, p, rng):
           self.p, self.rng, self.training = p, rng, True
       def forward(self, x):
           if not self.training:
               return x
           self.mask = (self.rng.random(x.shape) >= self.p) / (1 - self.p)   # 0 or 1/(1-p)
           return x * self.mask
       def backward(self, grad):
           return grad * self.mask       # dropped neurons get no blame
   ```
   Use it like `drop = Dropout(0.2, rng)` in `Sequential(Linear(2, 32, rng), ReLU(), drop, Linear(32, 1, rng), Sigmoid())`, and set `drop.training = False` before drawing the boundary. Training accuracy jumps around a bit more (that randomness is the point: it stops the network relying on any one neuron), and it still reaches 100%.
   </details>
3. Add **momentum** to `step`: keep a running "velocity" for each parameter (`v = 0.9 * v + grad`) and step with it (`p -= lr * v`). Does training speed up?
   <details><summary>Solution</summary>

   Replace `Sequential.step` with:
   ```python
   def step(self, lr, momentum=0.9):
       for layer in self.layers:
           if not hasattr(layer, "velocity"):
               layer.velocity = [np.zeros_like(p) for p in layer.params]
           for p, g, v in zip(layer.params, getattr(layer, "grads", []), layer.velocity):
               v *= momentum
               v += g
               p -= lr * v
   ```
   Yes, a lot. In our test on the moons (same `lr = 0.3`), plain SGD was at 97% accuracy after 300 epochs; with momentum the loss was already 0.0005 and accuracy 100%. Like a ball rolling downhill, momentum keeps moving in a consistent direction and speeds up on long gentle slopes. (Try 3,000 epochs with momentum too: if it ever explodes, lower `lr`.)
   </details>

## Check yourself
1. What two things does `Linear.backward` do, and why does it need `self.x`?
2. Why does `Sequential.backward` go through the layers in reverse?
3. Why is `step()` a separate phase instead of updating weights inside `backward()`?
4. Why use binary cross-entropy instead of squared error for a yes/no output?

<details><summary>Answers</summary>

1. It stores the gradients for its own weights (`dW = x.T @ grad`, `db = grad.sum(0)`) and returns the gradient for its input (`grad @ W.T`). `dW` depends on the input that went in, so it must be remembered from the forward pass.
2. Blame starts at the loss (the end) and each layer needs the gradient of the layer *after* it before it can compute its own: that's the chain rule in order.
3. `backward` uses the weights (`grad @ W.T`) to pass blame to earlier layers; changing them halfway would mix old and new weights. Keeping the update separate also lets you swap optimizers (SGD, momentum, Adam) without touching the layers. PyTorch does the same: `loss.backward()` then `optimizer.step()`.
4. Its penalty grows without limit as a confident prediction gets more wrong (`-log(0.01)` is big), and combined with a sigmoid its gradient stays strong, so learning doesn't stall when outputs are near 0 or 1.
</details>

## Learn more (optional)
- CS231n notes on neural networks (Stanford): https://cs231n.github.io/neural-networks-1/
- Building a neural network from scratch (no libraries): https://www.youtube.com/results?search_query=building+a+neural+network+from+scratch+numpy+samson+zhang

## Next
→ [2.5 · Same network in PyTorch: does your math match?](../05-same-network-in-pytorch-compare)
