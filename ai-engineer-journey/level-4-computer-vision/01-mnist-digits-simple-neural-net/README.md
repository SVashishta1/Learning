# 4.1 · MNIST digits: a simple neural net

**What you build:** a network that reads handwritten digits (0–9) with ~97% accuracy after 3 epochs (about a minute on a laptop), saved to `mnist_mlp.pt`.
**Like you're 10:** you show a kid 60,000 flashcards of handwritten numbers. They start guessing randomly, but every wrong guess teaches them a little. After 3 rounds through the deck they're almost always right.

## Run it
```bash
cd level-4-computer-vision/01-mnist-digits-simple-neural-net
pip install -r requirements.txt
python train_mnist.py --smoke     # quick wiring check, no download
python train_mnist.py             # the real thing (downloads MNIST to ./data)
```
At the end it prints a test digit as ASCII art with the model's guess.

## Key ideas
- **Tensor** = a NumPy array that can live on a GPU and track gradients.
- **Dataset + DataLoader** serve **mini-batches** of 64 images, shuffled every epoch.
- **Epoch** = one pass through all training images.
- **CrossEntropyLoss** takes the 10 raw scores ("logits") and punishes low probability on the right digit.
- **`model.train()` / `model.eval()` and `torch.no_grad()`:** remember these for every project.
- The training loop is the same 4 steps you built by hand in Level 2. PyTorch just does the calculus.

## Your turn
1. Add `nn.Dropout(0.2)` after each ReLU. Does test accuracy change?
2. Train for 10 epochs. Plot train vs. test accuracy per epoch. Do you see overfitting?
3. Swap MNIST for `datasets.FashionMNIST` (clothes instead of digits); nothing else changes!

## Watch
- But what is a neural network? (uses MNIST as its example, 3Blue1Brown): https://www.youtube.com/results?search_query=3blue1brown+but+what+is+a+neural+network
- PyTorch quickstart (also MNIST-style): https://pytorch.org/tutorials/beginner/basics/quickstart_tutorial.html
