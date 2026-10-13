# 2.6 · Micrograd: build an autograd engine

**What you build:** your own version of the magic behind `loss.backward()`. A `Value` class remembers how every number was computed. Then a 100-line engine computes **every gradient automatically**, and you train a small neural net with it.
**Like you're 10:** every number keeps a **family tree** (who its parents were and how they were combined). When the final score comes in, the blame travels back down the tree, and each ancestor gets its fair share.

## Run it
```bash
cd level-2-neural-nets-from-scratch/06-micrograd-autograd-engine
python demo.py            # no installs needed; torch is optional for the cross-check
```

## Files
- `engine.py`: the `Value` class. Each operation (`+`, `*`, `**`, `tanh`, `relu`) stores a tiny `_backward` function with its *local* derivative. `backward()` sorts the graph topologically and calls them in reverse.
- `nn.py`: `Neuron`, `Layer` and `MLP` built from `Value`s.
- `demo.py`: checks gradients by hand, trains an MLP, and compares with PyTorch.

## Key ideas
- **Local derivative × upstream gradient** (`self.grad += local * out.grad`). That one line *is* the chain rule.
- **`+=`, not `=`:** if a value is used twice, gradients from both uses must add up. (This is also why PyTorch needs `zero_grad()`.)
- **Topological order:** a node's gradient is final only after every node that used it has sent its share.
- PyTorch does exactly this, but on **tensors** (millions of numbers per node) instead of single scalars.

## Your turn
1. Add `exp()` and `log()` operations to `Value` with their derivatives.
2. Visualise the graph with `graphviz` (Karpathy shows how in the video).
3. Train the MLP on the two-moons data from 2.4, using a hinge or cross-entropy loss.

## Watch (this is THE video for this level)
- The spelled-out intro to neural networks and backpropagation: building micrograd (Karpathy): https://www.youtube.com/watch?v=VMj-3S1tku0
- Original code: https://github.com/karpathy/micrograd
