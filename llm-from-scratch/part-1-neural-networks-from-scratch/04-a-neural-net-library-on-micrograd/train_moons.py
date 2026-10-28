"""Lesson 04, part 2: a real (small) classification job: the "two moons" dataset.

100 dots in 2-D, shaped like two interlocking half-moons. Class -1 = top moon, class +1 = bottom moon.
A straight line can't separate them; a 2 -> 16 -> 16 -> 1 network can.
Pure Python, so it is slow-ish: about a minute on a laptop.
"""
import math
import random

from nn import MLP


def make_moons(n=100, noise=0.1, seed=1):
    """Two interleaving half circles (the same shape as scikit-learn's make_moons)."""
    rng = random.Random(seed)
    xs, ys = [], []
    for i in range(n):
        if i < n // 2:     # top moon: a half circle centred at (0, 0)
            angle = math.pi * i / (n // 2 - 1)
            x, y, label = math.cos(angle), math.sin(angle), -1.0
        else:              # bottom moon: flipped and shifted right/down
            angle = math.pi * (i - n // 2) / (n - n // 2 - 1)
            x, y, label = 1 - math.cos(angle), 0.5 - math.sin(angle), 1.0
        xs.append([x + rng.gauss(0, noise), y + rng.gauss(0, noise)])
        ys.append(label)
    return xs, ys


def loss_fn(model, xs, ys, alpha=1e-4):
    scores = [model(x) for x in xs]
    # "Max-margin" (hinge) loss: zero once a point is on the right side by a margin of 1.
    data_loss = sum((1 + -y * s).relu() for y, s in zip(ys, scores)) / len(ys)
    # L2 regularisation: a small penalty for big weights keeps the boundary smooth.
    reg_loss = alpha * sum(p * p for p in model.parameters())
    accuracy = sum((s.data > 0) == (y > 0) for y, s in zip(ys, scores)) / len(ys)
    return data_loss + reg_loss, accuracy


def ascii_plot(model, xs, ys, width=60, height=22):
    """Draw the decision regions with characters: '.' = model says -1, ' ' = model says +1."""
    x_min, x_max, y_min, y_max = -1.5, 2.5, -1.0, 1.5
    grid = []
    for row in range(height):
        y = y_max - (y_max - y_min) * row / (height - 1)
        line = []
        for col in range(width):
            x = x_min + (x_max - x_min) * col / (width - 1)
            line.append("." if model([x, y]).data < 0 else " ")
        grid.append(line)
    for (x, y), label in zip(xs, ys):     # put the real points on top
        col = round((x - x_min) / (x_max - x_min) * (width - 1))
        row = round((y_max - y) / (y_max - y_min) * (height - 1))
        if 0 <= row < height and 0 <= col < width:
            grid[row][col] = "o" if label < 0 else "x"
    print("+" + "-" * width + "+")
    for line in grid:
        print("|" + "".join(line) + "|")
    print("+" + "-" * width + "+")
    print("o = top moon (-1)   x = bottom moon (+1)   dotted area = where the model says -1")


if __name__ == "__main__":
    random.seed(1337)
    xs, ys = make_moons()
    model = MLP(2, [16, 16, 1], activation="relu", last_activation=None)
    print(f"model has {len(model.parameters())} parameters")

    for step in range(100):
        loss, acc = loss_fn(model, xs, ys)
        model.zero_grad()
        loss.backward()
        lr = 1.0 - 0.9 * step / 100            # learning-rate decay: big steps first, small steps later
        for p in model.parameters():
            p.data -= lr * p.grad
        if step % 10 == 0 or step == 99:
            print(f"step {step:3d}  loss {loss.data:.4f}  accuracy {acc:.0%}")

    ascii_plot(model, xs, ys)
