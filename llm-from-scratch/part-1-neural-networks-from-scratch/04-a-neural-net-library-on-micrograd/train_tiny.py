"""Lesson 04, part 1: train small MLPs with our own library.

  A) the 4-example dataset from the video (3 inputs -> 1 target each)
  B) XOR, the puzzle a single neuron could NOT learn in lesson 02
"""
import random

from nn import MLP


def train(model, xs, ys, steps, lr, report_every):
    for step in range(steps + 1):
        preds = [model(x) for x in xs]                                  # 1. forward pass
        loss = sum((p - y) ** 2 for p, y in zip(preds, ys)) / len(ys)   # 2. mean squared error
        model.zero_grad()                                               # 3. clear old grads
        loss.backward()                                                 # 4. backprop: fill every .grad
        for p in model.parameters():                                    # 5. step downhill
            p.data -= lr * p.grad
        if step % report_every == 0:
            print(f"  step {step:3d}  loss {loss.data:.5f}")
    return [model(x).data for x in xs]


random.seed(1337)

print("A) the video's tiny dataset")
xs = [[2.0, 3.0, -1.0], [3.0, -1.0, 0.5], [0.5, 1.0, 1.0], [1.0, 1.0, -1.0]]
ys = [1.0, -1.0, -1.0, 1.0]
model = MLP(3, [4, 4, 1], activation="tanh", last_activation="tanh")
print(" ", model)
print(f"  number of parameters: {len(model.parameters())}")
preds = train(model, xs, ys, steps=50, lr=0.1, report_every=10)
print("  predictions:", [round(p, 3) for p in preds], " targets:", ys)

print("\nB) XOR with a hidden layer (targets -1 = 'off', +1 = 'on')")
xs = [[0.0, 0.0], [0.0, 1.0], [1.0, 0.0], [1.0, 1.0]]
ys = [-1.0, 1.0, 1.0, -1.0]
model = MLP(2, [4, 1], activation="tanh", last_activation="tanh")
print(f"  number of parameters: {len(model.parameters())}")
preds = train(model, xs, ys, steps=200, lr=0.1, report_every=50)
for x, y, p in zip(xs, ys, preds):
    print(f"  {x} -> {p:+.3f} (target {y:+.0f}) {'right' if (p > 0) == (y > 0) else 'WRONG'}")
print("Two layers can bend the boundary, so XOR is solved.")
