# 2.4 · Your own mini framework: Layer classes

**What you build:** `tinyframe.py`, a mini PyTorch with `Linear`, `ReLU`, `Tanh`, `Sigmoid`, `Sequential` and an SGD step. Then you train it on XOR and on a curvy "two moons" dataset, and draw the boundary it learned.
**Like you're 10:** in 2.3 you built a car by welding every part by hand. Now you make **LEGO bricks** (layers) that snap together. Each brick knows two tricks: pass the ball forward, and pass the blame backward.

## Run it
```bash
cd level-2-neural-nets-from-scratch/04-mini-framework-layer-classes
pip install -r requirements.txt
python train_moons.py
```
You'll see accuracy climb to ~100%, a text-art map of the two regions, and `moons_boundary.png`.

## Key ideas
- **Every layer = forward + backward.** `Linear.backward` stores `dW, db` and returns the gradient for the layer before it. This is *exactly* PyTorch's design (`nn.Module` plus autograd).
- **Sequential** chains layers; `backward` walks them in reverse.
- **Optimizer step** is separate from backward: compute all gradients first, then update.
- **Cross-entropy loss** beats squared error for classification: it punishes confident wrong answers hard.
- **Initialization matters:** scaled random weights keep signals healthy through many layers.

## Your turn
1. Add a `Dropout(p)` layer: in forward, randomly zero a fraction `p` of values during training.
2. Add **momentum** to `step` (keep a running average of gradients). Does training speed up?
3. Generate a spiral dataset (3 arms) and add a softmax output for 3 classes. (Harder, but it's the classic CS231n exercise.)

## Watch
- CS231n notes on neural networks (Stanford): https://cs231n.github.io/neural-networks-1/
- Building a neural network from scratch (no libraries): https://www.youtube.com/results?search_query=building+a+neural+network+from+scratch+numpy+samson+zhang
