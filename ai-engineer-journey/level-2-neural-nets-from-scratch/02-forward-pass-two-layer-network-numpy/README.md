# 2.2 · Forward pass: a two-layer network in NumPy

**What you build:** you hand-code a network (2 inputs → 3 hidden neurons → 1 output) and pass numbers through it, first one neuron longhand, then a full layer as a matrix multiply, then a batch of 4 examples at once.
**Like you're 10:** a relay race. Each runner (neuron) gets the baton (numbers), adds their own style (weights and bias), and passes it on. The last runner crosses the finish line with the answer.

## Run it
```bash
cd level-2-neural-nets-from-scratch/02-forward-pass-two-layer-network-numpy
pip install -r requirements.txt
python forward_pass.py
```

## Key ideas
- **Neuron:** `sigmoid(sum(inputs * weights) + bias)`.
- **Layer = matrix multiply:** `X @ W` computes *every* neuron for *every* example in one line. This is why GPUs (great at matrix multiplies) power AI.
- **Shapes are everything:** `(examples, inputs) @ (inputs, neurons) → (examples, neurons)`. Most deep learning bugs are shape bugs. Print `.shape` often!
- **Activation (sigmoid):** without it, stacking layers would collapse into one big linear function. It adds the "bend" that lets networks learn curves.

## Your turn
1. Replace `sigmoid` with `relu = np.maximum(0, z)` for the hidden layer. How do the outputs change?
2. Add a third layer with 2 neurons. What shapes must `W3` and `b3` have?
3. Draw the network on paper with all 9 + 3 weights labelled. Compute `h[1]` for input `[1, 0]` by hand.

## Watch
- But what is a neural network? (3Blue1Brown): https://www.youtube.com/results?search_query=3blue1brown+but+what+is+a+neural+network
- NumPy for beginners: https://numpy.org/doc/stable/user/absolute_beginners.html
