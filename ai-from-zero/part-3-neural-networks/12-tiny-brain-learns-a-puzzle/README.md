# 12 · A tiny brain learns a puzzle

**What you'll build:** a 2-layer neural network that teaches itself the XOR puzzle (answer 1 only when exactly one input is 1). It starts by guessing randomly and ends up almost perfect.
**Time:** ~45 min · **Builds on:** [11 · One neuron learns](../11-one-neuron-learns) · **Needs:** `numpy`

## Why this matters
One knob can only learn straight-line rules. Real problems (spotting a face, reading a word) need curvy, combined rules, and **hidden layers** are how networks get them. The "blame" maths you'll see here, **backpropagation**, is the exact method used to train every modern network, including the ones behind ChatGPT and Claude.

## What you'll learn
- **Layer:** a group of neurons that all look at the same inputs; stacking layers lets a network combine simple patterns into complex ones.
- **Hidden layer:** a layer in the middle, between the inputs and the answer; it invents its own helpful in-between features.
- **Activation ("squash"):** a function that bends each neuron's output (here into 0 to 1), so the network isn't stuck with straight lines.
- **Backpropagation ("blame"):** working out, from the final mistake, how much each knob in each layer was responsible.

## Before you start
- Install numpy (fast maths on whole tables of numbers), with your virtual environment on:
  ```bash
  pip install numpy
  ```
  Or install everything for Part 3 at once: `pip install numpy torch torchvision pillow fastapi "uvicorn[standard]"`
- No API key needed.

## Run it
1. Open a terminal in the `ai-from-zero` folder.
2. Run:
   ```bash
   cd part-3-neural-networks/12-tiny-brain-learns-a-puzzle
   python tiny_brain.py
   ```

### What you should see
```
round     0: average miss 0.504
round  2500: average miss 0.037
round  5000: average miss 0.025
round  7500: average miss 0.020
round 10000: average miss 0.017

What it learned:
  0, 0  →  0.03   (rounds to 0)
  0, 1  →  0.98   (rounds to 1)
  1, 0  →  0.98   (rounds to 1)
  1, 1  →  0.01   (rounds to 0)
```
It takes under a second. At round 0 the average miss is about 0.5: pure guessing. By the end, every answer rounds to the right one: 0, 1, 1, 0. Your numbers match these exactly, because `np.random.seed(0)` makes the "random" start the same every time.

## How it works
**The puzzle.** XOR means "one or the other, but not both":
```
  0,0 → 0     0,1 → 1     1,0 → 1     1,1 → 0
```
Picture the four inputs as corners of a square. The two 1-answers sit on opposite corners. You can't draw **one** straight line that puts both 1s on one side and both 0s on the other. A single neuron can only draw one straight line, so it can't solve XOR. A hidden layer can combine several lines.

**The network:**
```
 input 1 ─┐       ┌─ hidden 1 ─┐
          ├─ all ─┼─ hidden 2 ─┼─ all ─→ answer
 input 2 ─┘       ├─ hidden 3 ─┤
                  └─ hidden 4 ─┘
   knobs_1: 2×4 = 8 knobs       knobs_2: 4×1 = 4 knobs
```

1. **Data.** `inputs` holds the 4 input pairs, and `answers` the 4 correct answers, as numpy tables (arrays).
2. **`squash`** is the sigmoid function, `1 / (1 + e^-x)`. It turns any number into something between 0 and 1, like a dimmer switch.
3. **Knobs.** `knobs_1 = np.random.randn(2, 4)` makes a 2×4 table of random starting knobs (each input → each hidden neuron). `knobs_2` is 4×1 (each hidden neuron → the answer).
4. **GUESS.** `inputs @ knobs_1` multiplies the table of inputs by the table of knobs (the `@` sign means "matrix multiply": every input times every knob, added up per neuron). That goes through `squash` to make `hidden`. The same again with `knobs_2` gives `guess`. All 4 examples are done at once.
5. **BLAME.** `mistake = guess - answers`, just like project 11. Then:
   - `blame_2` says how much each knob in layer 2 contributed to the mistake.
   - `blame_hidden` passes the blame **backwards** through layer 2 to the hidden neurons (that's why it's called *back*propagation).
   - `blame_1` turns that into blame for each knob in layer 1.

   The `guess * (1 - guess)` and `hidden * (1 - hidden)` parts are the slope of `squash`. You don't need to follow the calculus: in the next project PyTorch writes these three lines for you.
6. **NUDGE.** `knobs_2 -= 1.0 * blame_2` and the same for `knobs_1`. The `1.0` is the step size (learning rate), as in project 11.
7. **Repeat** 10,001 times, printing the average miss every 2,500 rounds, then show what it learned.

## If something goes wrong
- **`ModuleNotFoundError: No module named 'numpy'`** → turn on your virtual environment, then `pip install numpy`.
- **`RuntimeWarning: overflow encountered in exp`** → you set a very large step size or very large starting knobs. Put the `1.0` step sizes back.
- **Some answers round the wrong way** → you changed the number of hidden neurons or the seed. Small networks sometimes get stuck; run more rounds, or try another `np.random.seed(...)` number.
- **`ValueError: matmul: Input operand 1 has a mismatch`** → the knob table sizes don't line up. The number of columns in `knobs_1` must equal the number of rows in `knobs_2` (for example `(2, 4)` and `(4, 1)`).

## Try this
1. **Teach it AND instead.** Change the answers to `[[0], [0], [0], [1]]` (1 only when both inputs are 1).
   <details><summary>Hint</summary>

   It learns this easily (0.01, 0.01, 0.01, 0.99). AND *can* be split by one straight line, so even one neuron could do it.
   </details>
2. **Shrink the hidden layer.** Change `randn(2, 4)` and `randn(4, 1)` to `randn(2, 2)` and `randn(2, 1)`. Does it still learn? Now also try `np.random.seed(1)`, `seed(2)` and `seed(3)`.
   <details><summary>Hint</summary>

   With seed 0 it still gets there (about 0.93 for the 1s). With other seeds it often gets stuck and rounds some answers wrong. More hidden neurons give the network more ways to find a solution, which is one reason real networks are big.
   </details>
3. **Stop early.** Make it stop as soon as the average miss drops below 0.05, and print how many rounds that took.
   <details><summary>Solution</summary>

   Add these lines inside the loop, just before the `if round_number % 2500 == 0:` line:
   ```python
       if np.abs(mistake).mean() < 0.05:
           print(f"Good enough after {round_number} rounds!")
           break
   ```
   It prints `Good enough after 1535 rounds!`. Stopping when the model is good enough is a real technique called **early stopping**.
   </details>

## Check yourself
1. Why can't a single neuron learn XOR?
2. What does the hidden layer add?
3. In which direction does the blame travel, and why is it called "backpropagation"?
4. Why does the code call `np.random.seed(0)`?

<details><summary>Answers</summary>

1. One neuron can only split its inputs with one straight line, and XOR's 1-answers are on opposite corners, so no single line separates them.
2. Extra neurons that each learn their own simple pattern; the output neuron combines them into a more complex rule.
3. Backwards: from the final mistake, through layer 2, to layer 1. Each layer's blame is worked out from the blame of the layer after it.
4. So the "random" starting knobs are the same every run, which makes results repeatable (and lets you compare with this README).
</details>

## Learn more (optional)
- 3Blue1Brown, "But what is a neural network?": https://www.youtube.com/results?search_query=3blue1brown+but+what+is+a+neural+network
- 3Blue1Brown, "What is backpropagation really doing?": https://www.youtube.com/results?search_query=3blue1brown+what+is+backpropagation+really+doing

## Next
→ [13 · Same brain in PyTorch](../13-same-brain-in-pytorch)
