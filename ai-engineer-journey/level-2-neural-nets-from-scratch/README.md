# Level 2 · Neural networks from scratch: a student learning from mistakes

A neural network is a student who:
1. **guesses** an answer (forward pass),
2. **checks** how wrong it was (loss),
3. figures out **which knobs caused the mistake** (backpropagation = gradients),
4. **nudges** those knobs a little (gradient descent),
5. repeats thousands of times.

That's it. Every model up to GPT is this loop at a bigger scale. You'll build it with your own hands before letting PyTorch do it for you.

| # | Project | You'll understand |
|---|---------|-------------------|
| 2.1 | [One neuron learns y = 2x](01-one-neuron-learns-y-equals-2x) | loss, gradient, learning rate, with zero libraries |
| 2.2 | [Forward pass, two layers](02-forward-pass-two-layer-network-numpy) | matrices, shapes, activations |
| 2.3 | [Backprop by hand learns XOR](03-backprop-by-hand-learns-xor) | the chain rule, gradient checking |
| 2.4 | [Your own mini framework](04-mini-framework-layer-classes) | how PyTorch is organised inside |
| 2.5 | [Same network in PyTorch](05-same-network-in-pytorch-compare) | autograd; proof your math matches |
| 2.6 | [Micrograd autograd engine](06-micrograd-autograd-engine) | how `loss.backward()` really works |

```bash
pip install numpy matplotlib torch   # torch is only needed for 2.5 and 2.6
```

**The one playlist for this level:** Karpathy's *Neural Networks: Zero to Hero* https://www.youtube.com/playlist?list=PLAqhIrjkxbuWI23v9cThsA9GvCAUhRvKZ
**Visual intuition:** 3Blue1Brown's neural network series https://www.youtube.com/playlist?list=PLZHQObOWTQDNU6R1_67000Dx_ZCJB-3pi
