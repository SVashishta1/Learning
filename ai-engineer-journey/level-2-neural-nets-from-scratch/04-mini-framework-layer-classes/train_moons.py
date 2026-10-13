"""Train tinyframe on XOR, then on a curvy 'two moons' dataset, and draw what it learned."""
import numpy as np

from tinyframe import Linear, ReLU, Sequential, Sigmoid, Tanh, bce_loss

rng = np.random.default_rng(0)


def train(model, X, y, epochs, lr, label):
    for epoch in range(1, epochs + 1):
        p = model(X)
        loss, grad = bce_loss(p, y)
        model.backward(grad)
        model.step(lr)
        if epoch % (epochs // 5) == 0:
            acc = ((p > 0.5) == y).mean()
            print(f"[{label}] epoch {epoch:5d} | loss {loss:.4f} | accuracy {acc:.0%}")


# 1) XOR, in 4 lines thanks to the framework
X = np.array([[0, 0], [0, 1], [1, 0], [1, 1]], float)
y = np.array([[0], [1], [1], [0]], float)
xor_net = Sequential(Linear(2, 8, rng), Tanh(), Linear(8, 1, rng), Sigmoid())
train(xor_net, X, y, 2000, 0.5, "xor")

# 2) Two moons: 200 points shaped like two interlocking bananas
n = 100
t = rng.uniform(0, np.pi, n)
moon_a = np.c_[np.cos(t), np.sin(t)] + rng.normal(0, 0.1, (n, 2))
moon_b = np.c_[1 - np.cos(t), 0.5 - np.sin(t)] + rng.normal(0, 0.1, (n, 2))
X = np.vstack([moon_a, moon_b])
y = np.r_[np.zeros(n), np.ones(n)].reshape(-1, 1)

net = Sequential(Linear(2, 16, rng), ReLU(), Linear(16, 16, rng), ReLU(), Linear(16, 1, rng), Sigmoid())
train(net, X, y, 3000, 0.3, "moons")

# Draw the decision boundary as text art (no matplotlib needed)...
print("\nWhat the network thinks (A = class 0, B = class 1):")
for yy in np.linspace(1.4, -0.9, 14):
    row = net(np.c_[np.linspace(-1.3, 2.3, 60), np.full(60, yy)])
    print("".join("B" if v > 0.5 else "A" for v in row.ravel()))

# ...and as a picture if matplotlib is installed
try:
    import matplotlib.pyplot as plt
    gx, gy = np.meshgrid(np.linspace(-1.5, 2.5, 200), np.linspace(-1, 1.5, 200))
    zz = net(np.c_[gx.ravel(), gy.ravel()]).reshape(gx.shape)
    plt.contourf(gx, gy, zz, levels=20, cmap="RdBu", alpha=0.6)
    plt.scatter(X[:, 0], X[:, 1], c=y.ravel(), cmap="RdBu", edgecolors="k")
    plt.title("tinyframe decision boundary")
    plt.savefig("moons_boundary.png", dpi=120)
    print("\nSaved moons_boundary.png")
except ImportError:
    pass
