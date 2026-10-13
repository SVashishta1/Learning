# A tiny brain with 2 layers learns the "XOR" puzzle: answer 1 only if EXACTLY ONE input is 1.
#   0,0 -> 0    0,1 -> 1    1,0 -> 1    1,1 -> 0
# One neuron can't solve this. A small hidden layer can.
import numpy as np   # numpy = fast maths on whole tables of numbers at once

np.random.seed(0)
inputs = np.array([[0, 0], [0, 1], [1, 0], [1, 1]])
answers = np.array([[0], [1], [1], [0]])

squash = lambda x: 1 / (1 + np.exp(-x))     # squeezes any number to between 0 and 1

knobs_1 = np.random.randn(2, 4)             # layer 1: 2 inputs -> 4 hidden neurons
knobs_2 = np.random.randn(4, 1)             # layer 2: 4 hidden neurons -> 1 answer

for round_number in range(10_001):
    # GUESS: pass the inputs through both layers
    hidden = squash(inputs @ knobs_1)       # @ = "multiply the table of inputs by the table of knobs"
    guess = squash(hidden @ knobs_2)

    # BLAME: how much did each knob contribute to the mistake? (This is "backpropagation".)
    mistake = guess - answers
    blame_2 = hidden.T @ (mistake * guess * (1 - guess))
    blame_hidden = (mistake * guess * (1 - guess)) @ knobs_2.T * hidden * (1 - hidden)
    blame_1 = inputs.T @ blame_hidden

    # NUDGE every knob against its blame
    knobs_2 -= 1.0 * blame_2
    knobs_1 -= 1.0 * blame_1

    if round_number % 2500 == 0:
        print(f"round {round_number:5d}: average miss {np.abs(mistake).mean():.3f}")

print("\nWhat it learned:")
for x, g in zip(inputs, guess):
    print(f"  {x[0]}, {x[1]}  →  {g[0]:.2f}   (rounds to {round(g[0])})")
