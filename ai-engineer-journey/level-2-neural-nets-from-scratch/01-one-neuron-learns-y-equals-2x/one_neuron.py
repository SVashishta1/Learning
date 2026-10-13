"""Project 2.1: one 'neuron' with one knob (w) learns that y = 2x. No libraries at all.

The student's rule is:   prediction = w * x
We start with a silly guess (w = 0.5) and let the mistakes teach us.
"""
import random

random.seed(0)
data = [(x, 2 * x) for x in [1, 2, 3, 4, 5]]   # the answers we want to learn from


# ---- Step 0: what IS a gradient? Nudge the knob and watch the error change. ----
def total_error(w):
    # Mean squared error: average of (prediction - truth)^2. Squaring makes all mistakes positive.
    return sum((w * x - y) ** 2 for x, y in data) / len(data)

w = 0.5
nudge = 0.0001
slope = (total_error(w + nudge) - total_error(w)) / nudge
print(f"At w={w}: error={total_error(w):.2f}. Nudging w up changes error by {slope:.2f} per unit.")
print("Negative slope => increasing w REDUCES error. So we should move w UP.\n")

# ---- Step 1: the learning loop ----
w = 0.5
learning_rate = 0.01   # how big a step to take. Too big = overshoot, too small = slow.

for step in range(1, 61):
    # gradient = d(error)/dw, worked out with calculus: average of 2 * (w*x - y) * x
    grad = sum(2 * (w * x - y) * x for x, y in data) / len(data)
    w = w - learning_rate * grad            # step DOWNHILL (opposite to the gradient)
    if step in (1, 2, 3, 5, 10, 20, 40, 60):
        bar = "█" * int(total_error(w) * 2)
        print(f"step {step:2d} | w = {w:.4f} | error = {total_error(w):8.4f} {bar}")

print(f"\nLearned w = {w:.4f} (truth is 2). Prediction for x=10: {w * 10:.2f}")

# ---- Step 2: try a BAD learning rate to see why it matters ----
w = 0.5
for _ in range(10):
    w -= 0.1 * sum(2 * (w * x - y) * x for x, y in data) / len(data)
print(f"\nWith learning_rate=0.1 after 10 steps, w = {w:.1f}  <- exploded! Steps too big overshoot the valley.")
