# 2.6 · Micrograd: build an autograd engine

**What you'll build:** your own version of the magic behind `loss.backward()`. A `Value` class remembers how every number was computed; an ~80-line engine then computes **every gradient automatically**, and you train a small neural network with it, in plain Python.
**Like you're 10:** every number keeps a **family tree** (who its parents were and how they were combined). When the final score comes in, the blame travels back down the tree, and each ancestor gets its fair share.
**Time:** ~3 h · **Builds on:** [2.5 · Same network in PyTorch](../05-same-network-in-pytorch-compare) · **Needs:** nothing extra (PyTorch optional, for a cross-check)

## Why this matters
In 2.3 you wrote gradients by hand; in 2.5 PyTorch did it for you. This project shows *how* PyTorch does it: build a graph of operations while computing, then walk it backwards applying one tiny rule per operation. Every deep-learning framework (PyTorch, JAX, TensorFlow) is this idea scaled up to tensors and GPUs. After this, `loss.backward()` holds no mystery, and that understanding is what lets engineers debug training and design new layers.

## What you'll learn
- **Computation graph:** every result remembers its inputs (`_parents`) and the operation that made it (`_op`).
- **Local derivative:** each operation only knows its own tiny rule (for `a * b`, the derivative with respect to `a` is `b`).
- **Chain rule as code:** `self.grad += local_derivative * out.grad`. That one line *is* backpropagation.
- **Topological order:** process a node only after every node that used it has passed back its share of the blame.
- **Gradient accumulation:** `+=`, not `=`, because a value used twice gets blame from both uses (and why PyTorch needs `zero_grad()`).

## Before you start
- Nothing to install: `engine.py`, `nn.py` and `demo.py` use plain Python.
- Optional: `pip install torch` (you have it from 2.5) for the PyTorch cross-check at the end of `demo.py`. Without it the demo prints a note and skips that part.
- No API key needed.

## Run it
```bash
cd level-2-neural-nets-from-scratch/06-micrograd-autograd-engine
python demo.py
```

### What you should see
```
L = -8.0
Value(a=2.0000, grad=6.0000)
Value(b=-3.0000, grad=-4.0000)
Value(c=10.0000, grad=-2.0000)
Value(f=-2.0000, grad=4.0000)
✅ hand-calculated gradients match

model has 41 parameters
step   1 | loss 3.09286
step  10 | loss 0.00021
step  50 | loss 0.00000
step 100 | loss 0.00000
predictions: [1.0, -1.0, -1.0, 1.0] targets: [1.0, -1.0, -1.0, 1.0]

PyTorch dz/dx = -24.0  | micrograd dz/dx = -24.0
✅ micrograd agrees with PyTorch
```
Three proofs that the engine works: the gradients of a small expression match the ones worked out by hand, a 41-parameter network learns its 4 targets almost perfectly, and a trickier expression gives exactly the same gradient as PyTorch.

## How it works
For the expression `L = (a*b + c) * f` from `demo.py`:
```
FORWARD (build the tree)                    BACKWARD (blame flows down)
a=2 ──┐                                      a.grad = e.grad * b = -2 * -3 =  6
      ├─ * ─► e=-6 ──┐                       b.grad = e.grad * a = -2 *  2 = -4
b=-3 ─┘              ├─ + ─► d=4 ──┐         e.grad = d.grad * 1           = -2
c=10 ────────────────┘             ├─ * ─► L=-8      c.grad = d.grad * 1   = -2
f=-2 ──────────────────────────────┘         d.grad = L.grad * f = 1 * -2  = -2
                                             f.grad = L.grad * d = 1 *  4  =  4
```
**`engine.py`**
1. **`Value.__init__`** stores `data` (the number), `grad` (starts at 0: "how much does the final output change if I change?"), `_parents` (the values it was made from), `_op` (which operation) and `_backward`, a small function that knows how to pass this value's grad on to its parents.
2. **Each operation** (`__add__`, `__mul__`, `__pow__`, `tanh`, `relu`) computes the result, creates `out = Value(..., (self, other), "op")`, and defines `out._backward` with its local derivative:
   - `+`: both parents get `out.grad` unchanged (derivative 1).
   - `*`: each parent gets the *other* parent's value times `out.grad`.
   - `** k`: `k * x ** (k - 1) * out.grad` (the power rule; `k` must be a plain number).
   - `tanh`: `(1 - t²) * out.grad`. `relu`: `out.grad` if the output was positive, else 0.
   Plain numbers are wrapped automatically (`other if isinstance(other, Value) else Value(other)`).
3. **Convenience operators** reuse those few rules: `-x` is `x * -1`, `a - b` is `a + (-b)`, `a / b` is `a * b ** -1`, and `__radd__`/`__rmul__`/`__rtruediv__` make `2 * x`, `2 + x` and `2 / x` work when the number comes first.
4. **`backward()`** first builds a **topological order** with the recursive `build(v)`: a node is appended only after all of its parents, so the list goes from inputs to output. It sets the output's `grad = 1.0` (the output changes 1:1 with itself), then calls `_backward()` on every node in **reverse** order, so each node has received blame from all its users before passing it on.

**`nn.py`**
5. **`Neuron`** has one random weight per input plus a bias, all `Value`s. Calling it computes `sum(w * x) + b` and applies `tanh` (or nothing, for the output layer). **`Layer`** is a list of neurons; **`MLP`** chains layers (here 3 → 4 → 4 → 1). Each class has `parameters()` so training can find every knob: same design as PyTorch's `nn.Module`.

**`demo.py`**
6. Part 1 builds `L = (a*b + c) * f`, calls `L.backward()`, and `assert`s the four gradients equal the hand calculation above.
7. Part 2 trains the MLP on 4 examples: forward (`model(x)` for each), squared-error loss, **zero the grads**, `loss.backward()`, then `p.data -= 0.05 * p.grad` for all 41 parameters. Exactly the loop you wrote with PyTorch in 2.5.
8. Part 3 computes `z = relu(2x + 2 + x) + 3 * relu(x * x)` at `x = -4` in both PyTorch and micrograd. The first `relu` is off (its input is -10), so only the second part counts: `dz/dx = 3 * 2x = -24` in both.

## If something goes wrong
- **`(install torch to cross-check against PyTorch)`** at the end → not an error: torch isn't installed, so part 3 was skipped. `pip install torch` to run it.
- **Gradients are double what you expect** → you called `backward()` twice, or forgot to reset `p.grad = 0.0` before it. Gradients add up (`+=`), on purpose.
- **`AssertionError: only plain-number powers`** → you wrote `x ** y` where `y` is a `Value`. This engine supports `x ** 2` or `x ** -1`, not a `Value` exponent (that would need a log rule, see exercise 1).
- **`RecursionError: maximum recursion depth exceeded`** in `backward()` → your graph is very deep (thousands of operations in a chain), and `build()` is recursive. Use smaller models/data here; real frameworks use tensors so graphs stay small.
- **Training is slow** → every number is a Python object, so micrograd is thousands of times slower than PyTorch. That's expected: it's built to be understood, not to be fast.

## Try this
1. Print the computation graph of `L` as an indented tree, showing each value, its grad and the operation that made it.
   <details><summary>Solution</summary>

   ```python
   def show(v, indent=0):
       print("  " * indent + f"{v.label or '?'} = {v.data:.4f}  (grad {v.grad:.4f})" + (f"  <- {v._op}" if v._op else ""))
       for p in v._parents:
           show(p, indent + 1)

   show(L)
   ```
   Output (the order of siblings may differ, because `_parents` is a set):
   ```
   L = -8.0000  (grad 1.0000)  <- *
     f = -2.0000  (grad 4.0000)
     d = 4.0000  (grad -2.0000)  <- +
       c = 10.0000  (grad -2.0000)
       e = -6.0000  (grad -2.0000)  <- *
         a = 2.0000  (grad 6.0000)
         b = -3.0000  (grad -4.0000)
   ```
   Karpathy's video draws the same tree as a picture with the `graphviz` library.
   </details>
2. Add `exp()` and `log()` operations to `Value`, with their derivatives, and check them against PyTorch.
   <details><summary>Solution</summary>

   Add these methods to the `Value` class:
   ```python
   def exp(self):
       out = Value(math.exp(self.data), (self,), "exp")
       def _backward():
           self.grad += out.data * out.grad          # d(e^x)/dx = e^x
       out._backward = _backward
       return out

   def log(self):
       out = Value(math.log(self.data), (self,), "log")
       def _backward():
           self.grad += (1 / self.data) * out.grad   # d(ln x)/dx = 1/x
       out._backward = _backward
       return out
   ```
   Check: `x = Value(2.0); y = x.exp() + x.log(); y.backward()` gives `x.grad = 7.889...` (`e² + 1/2`), the same as PyTorch's `x.grad` for `x.exp() + x.log()`. With `exp` and `log` you can build softmax and cross-entropy loss.
   </details>
3. Train an MLP on two-moons data (like 2.4) with a **hinge loss**: labels are -1 and +1, and the loss for each point is `relu(1 - label * score)`.
   <details><summary>Solution</summary>

   ```python
   import math, random
   from nn import MLP

   random.seed(0)
   pts = []
   for i in range(30):                      # 30 points per moon (micrograd is slow!)
       t = math.pi * i / 29
       pts.append(([math.cos(t) + random.gauss(0, 0.1), math.sin(t) + random.gauss(0, 0.1)], -1.0))
       pts.append(([1 - math.cos(t) + random.gauss(0, 0.1), 0.5 - math.sin(t) + random.gauss(0, 0.1)], 1.0))

   model = MLP(2, [8, 8, 1])
   for step in range(1, 101):
       scores = [model(x) for x, _ in pts]
       loss = sum((1 + -y * s).relu() for (_, y), s in zip(pts, scores)) * (1 / len(pts))
       for p in model.parameters():
           p.grad = 0.0
       loss.backward()
       for p in model.parameters():
           p.data -= 0.2 * p.grad
       if step % 20 == 0:
           acc = sum((s.data > 0) == (y > 0) for (_, y), s in zip(pts, scores)) / len(pts)
           print(f"step {step} | loss {loss.data:.4f} | accuracy {acc:.0%}")
   ```
   In our run, accuracy climbed from 87% to 95% in 100 steps (about half a minute). The hinge loss is 0 once a point is on the right side *with a margin* (`label * score >= 1`), so the network stops worrying about easy points and focuses on the hard ones near the boundary.
   </details>

## Check yourself
1. What does each `_backward` function need to know, and what does it *not* need to know?
2. Why `self.grad += ...` instead of `self.grad = ...`?
3. Why must `backward()` visit nodes in reverse topological order?
4. What's the main difference between micrograd and PyTorch's autograd?

<details><summary>Answers</summary>

1. Only its own local derivative and its output's `grad`. It doesn't need to know anything about the rest of the graph: the chain rule stitches the local pieces together.
2. A value can be used more than once (like `x` in `x * x` or in `2*x + x`). Each use sends back its own share of blame, and the total gradient is the sum.
3. A node's grad is only complete after every node that used it has added its share. Reverse topological order guarantees all users are processed before the node itself passes blame further back.
4. Micrograd works on single numbers (scalars); PyTorch works on tensors (whole arrays per node), written in fast C++/CUDA. The idea, building a graph and applying local derivatives in reverse, is the same.
</details>

## Learn more (optional)
- The spelled-out intro to neural networks and backpropagation: building micrograd (Karpathy). This is THE video for this level: https://www.youtube.com/watch?v=VMj-3S1tku0
- Original micrograd code: https://github.com/karpathy/micrograd

## Next
You've finished Level 2: you know what "learning" really is. Next you'll use ready-made models that still run most businesses.
→ [3.1 · House price predictor (linear regression)](../../level-3-classic-ml/01-house-price-predictor-linear-regression)
