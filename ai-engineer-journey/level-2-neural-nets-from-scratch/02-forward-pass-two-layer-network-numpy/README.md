# 2.2 · Forward pass: two-layer network in NumPy

**What you'll build:** a hand-coded network (2 inputs → 3 hidden neurons → 1 output) and you push numbers through it: first one neuron written out longhand, then a whole layer as a matrix multiply, then a batch of 4 examples at once.
**Like you're 10:** a relay race. Each runner (neuron) gets the baton (numbers), adds their own style (weights and bias), and passes it on. The last runner crosses the finish line with the answer.
**Time:** ~1 h · **Builds on:** [2.1 · One neuron learns y = 2x](../01-one-neuron-learns-y-equals-2x) · **Needs:** nothing extra

## Why this matters
The **forward pass** is what a model does every time you use it: ChatGPT answering, a photo app tagging faces, a spam filter scoring an email. It's nothing but multiplying by weights, adding biases and squashing, layer after layer. Writing it as matrix multiplies is also *why* AI runs on GPUs: they are machines built to do huge matrix multiplies fast.

## What you'll learn
- **Neuron:** `activation(sum(inputs * weights) + bias)`: a weighted vote, plus a default mood, then squashed.
- **Layer = matrix multiply:** `X @ W` computes every neuron for every example in one line.
- **Shapes:** `(examples, inputs) @ (inputs, neurons) → (examples, neurons)`. Most deep-learning bugs are shape bugs.
- **Activation function (sigmoid):** the "bend" that lets networks learn curves; without it, stacked layers collapse into one straight-line function.
- **Broadcasting:** NumPy adds a bias vector to every row of a matrix automatically.

## Before you start
```bash
cd level-2-neural-nets-from-scratch/02-forward-pass-two-layer-network-numpy
pip install -r requirements.txt
```
- `numpy`: fast arrays and matrix maths for Python.

No API key needed.

## Run it
```bash
python forward_pass.py
```

### What you should see
```
one neuron: z = 0.6 -> sigmoid(z) = 0.646
hidden layer: [0.646 0.426 0.646]  output: [0.573]

shapes: X (4, 2) -> H (4, 3) -> OUT (4, 1)
input [0. 0.] -> output 0.512
input [0. 1.] -> output 0.442
input [1. 0.] -> output 0.573
input [1. 1.] -> output 0.500

These outputs are random-ish because the weights are made up. In 2.3 we LEARN the weights.
```
Notice that the first hidden value (`0.646`) equals the single neuron above it: the matrix version computes exactly the same thing, just for all neurons at once. Also notice that the output for input `[1, 0]` (`0.573`) appears both in the single-example line and in the batch.

## How it works
```
x (2 numbers) ──► @ W1 + b1 ──► sigmoid ──► h (3 numbers) ──► @ W2 + b2 ──► sigmoid ──► output (1 number)
   shape (2,)       (2,3)  (3,)               shape (3,)         (3,1) (1,)               shape (1,)
```
1. **`sigmoid(z)`** = `1 / (1 + e^-z)` squashes any number into the range 0 to 1: big positive → almost 1, big negative → almost 0, zero → 0.5.
2. **Part 1, one neuron:** `x = [1.0, 0.0]`, weights `w = [0.5, -0.4]`, bias `b = 0.1`. The weighted sum is `1.0*0.5 + 0.0*(-0.4) + 0.1 = 0.6`, and `sigmoid(0.6) = 0.646`. A weight says "how much do I care about this input"; the bias is the neuron's default mood when inputs are zero.
3. **Part 2, a layer:** `W1` has shape `(2, 3)`: one row per input, one **column per neuron**. `x @ W1` (the `@` is matrix multiply) computes all three weighted sums at once, `+ b1` adds each neuron's bias, and `sigmoid` squashes all three. `h @ W2 + b2` then combines the 3 hidden values into 1 output. The `assert` proves neuron 0 matches the longhand formula.
4. **Part 3, a batch:** `X` has 4 rows, one per example. `X @ W1` is `(4, 2) @ (2, 3) → (4, 3)`: every neuron for every example, in one call. `b1` has shape `(3,)` and NumPy **broadcasts** it: it's added to each of the 4 rows.
5. **The shape rule:** in `A @ B`, the *inner* numbers must match (`(4, 2) @ (2, 3)`: both 2) and the result takes the *outer* ones (`(4, 3)`). When something breaks, print `.shape` first.

## If something goes wrong
- **`ModuleNotFoundError: No module named 'numpy'`** → activate your venv and run `pip install -r requirements.txt`.
- **`ValueError: matmul: Input operand 1 has a mismatch in its core dimension 0 ...`** → a shape bug: the inner sizes of `A @ B` don't match. Print `A.shape` and `B.shape`; you probably need `W.T` (transpose) or the other order.
- **Your new layer's output has the wrong shape** → check each weight matrix is `(inputs to this layer, neurons in this layer)` and each bias is `(neurons in this layer,)`.
- **`RuntimeWarning: overflow encountered in exp`** → you fed sigmoid a huge negative number (around -700). The result is still correct (0); it's a warning, not an error.

## Try this
1. Check the network by hand: compute `h[1]` for input `[1, 0]` with pencil and paper (or a calculator).
   <details><summary>Solution</summary>

   Neuron 1 uses column 1 of `W1` (`-0.3` and `0.9`) and bias `b1[1] = 0.0`:
   `z = 1 * (-0.3) + 0 * 0.9 + 0.0 = -0.3`, and `sigmoid(-0.3) = 1 / (1 + e^0.3) = 0.426`. That's the middle number of `hidden layer: [0.646 0.426 0.646]`.
   </details>
2. Replace `sigmoid` with ReLU, `relu = lambda z: np.maximum(0, z)`, for the hidden layer only (keep sigmoid on the output). How do the hidden values change?
   <details><summary>Solution</summary>

   Use `H = relu(X @ W1 + b1)` in part 3. The hidden values become:
   ```
   [[0.1 0.  0. ]
    [0.  0.9 0. ]
    [0.6 0.  0.6]
    [0.2 0.6 0.8]]
   ```
   ReLU keeps positive numbers as they are and turns negatives into exactly 0 (that neuron is "off" for that example). Sigmoid never gives exactly 0. ReLU is the most common hidden activation in modern networks because it's cheap and trains well in deep networks.
   </details>
3. Add a second hidden layer with 2 neurons, so the network becomes 2 → 3 → 2 → 1. What shapes must the new weights and biases have?
   <details><summary>Solution</summary>

   ```python
   rng = np.random.default_rng(0)
   W2, b2 = rng.normal(0, 1, (3, 2)), np.zeros(2)   # 3 hidden -> 2 hidden
   W3, b3 = rng.normal(0, 1, (2, 1)), np.zeros(1)   # 2 hidden -> 1 output
   H1 = sigmoid(X @ W1 + b1)      # (4, 3)
   H2 = sigmoid(H1 @ W2 + b2)     # (4, 2)
   OUT = sigmoid(H2 @ W3 + b3)    # (4, 1)
   ```
   Each weight matrix is `(neurons in the previous layer, neurons in this layer)`; each bias has one number per neuron in this layer.
   </details>

## Check yourself
1. In `W1` with shape `(2, 3)`, what do the 2 and the 3 mean?
2. What shape is `X @ W1` when `X` holds 10 examples with 2 inputs each?
3. Why do networks need an activation function like sigmoid between layers?
4. How many weights and biases does this 2 → 3 → 1 network have in total?

<details><summary>Answers</summary>

1. 2 = number of inputs to the layer (rows); 3 = number of neurons in the layer (columns).
2. `(10, 3)`: 10 examples, each with 3 hidden values.
3. Without it, layer after layer of "multiply and add" is still just one big "multiply and add" (a straight line). The bend from the activation lets the network represent curves and complicated rules.
4. `W1` has 2×3 = 6 weights, `b1` 3 biases, `W2` 3×1 = 3 weights, `b2` 1 bias: 13 numbers in total.
</details>

## Learn more (optional)
- But what is a neural network? (3Blue1Brown): https://www.youtube.com/results?search_query=3blue1brown+but+what+is+a+neural+network
- NumPy for absolute beginners: https://numpy.org/doc/stable/user/absolute_beginners.html

## Next
→ [2.3 · Backprop by hand: learn XOR](../03-backprop-by-hand-learns-xor)
