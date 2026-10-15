# 4.1 · MNIST digits: a simple neural net

**What you'll build:** a PyTorch network that reads handwritten digits (0–9) with about **97% accuracy** after 3 passes through the data (about a minute on a laptop), saved to `mnist_mlp.pt` so you can reuse it in 4.5.
**Like you're 10:** you show a kid 60,000 flashcards of handwritten numbers. They start guessing randomly, but every wrong guess teaches them a little. After 3 rounds through the deck they're almost always right.
**Time:** ~1 h · **Builds on:** [2.5 Same network in PyTorch](../../level-2-neural-nets-from-scratch/05-same-network-in-pytorch-compare) and [3.6 Churn predictor](../../level-3-classic-ml/06-churn-predictor-end-to-end-pipeline) · **Needs:** nothing extra (GPU optional, internet once for the ~12 MB dataset)

## Why this matters
This is the standard PyTorch training loop. Every image, text and audio model you'll train (including fine-tuning LLMs in Level 6) follows these same steps: load data in batches, predict, measure the loss, backpropagate, update, evaluate, save. MNIST is the "hello world" of computer vision because it's small enough to train in a minute, so you can focus on the loop itself.

## What you'll learn
- **Tensors**: PyTorch's arrays, like NumPy arrays that can run on a GPU and track gradients.
- **Dataset + DataLoader**: serving shuffled **mini-batches** of 64 images instead of one at a time.
- **The training loop**: forward → loss → `backward()` → `optimizer.step()`, the same 4 steps you did by hand in Level 2.
- **CrossEntropyLoss and logits**: how a network scores 10 possible answers and gets punished for being wrong.
- **`train()` / `eval()` and `torch.no_grad()`**: switching between learning mode and testing mode.

## Before you start
```bash
pip install -r requirements.txt
```
- `torch`: PyTorch, the deep-learning library (network, loss, optimizer, autograd).
- `torchvision`: ready-made image datasets (MNIST) and image transforms.

No API key needed. The first real run downloads MNIST (~12 MB) into a `data/` folder. No GPU needed: the script uses `cuda` (NVIDIA) or `mps` (Apple Silicon) automatically if you have one, otherwise the CPU.

## Run it
1. From the course root:
   ```bash
   cd level-4-computer-vision/01-mnist-digits-simple-neural-net
   pip install -r requirements.txt
   ```
2. Quick wiring check (a few seconds, random fake images, no download, nothing saved):
   ```bash
   python train_mnist.py --smoke
   ```
   Accuracy will be ~10% (random guessing on random noise). That's expected: you're only checking that nothing crashes.
3. The real thing (downloads MNIST, trains 3 epochs, saves `mnist_mlp.pt`):
   ```bash
   python train_mnist.py
   ```

### What you should see
```
device: cpu | parameters: 109,386
epoch 1 batch    0 | loss 2.324
epoch 1 batch  300 | loss 0.249
epoch 1 batch  600 | loss 0.204
epoch 1 batch  900 | loss 0.166
epoch 1 test accuracy: 96.06%
epoch 2 batch    0 | loss 0.151
...
epoch 3 batch  900 | loss 0.007
epoch 3 test accuracy: 97.08%
saved mnist_mlp.pt



   @@@@@@@@
      +++:@
         @*
        =@
        @=
       *@
       @-
      @@
     +@=
     @@
model says: 7 | truth: 7
```
What to look at:
- **Loss starts at ~2.3.** That's what random guessing among 10 digits gives (ln 10 ≈ 2.30). It drops fast as the network learns.
- **Test accuracy ~97%** on 10,000 digits the network never trained on.
- **The ASCII art** is the first test image, drawn with characters, and the model's guess for it.

## How it works
```
28×28 image ─► Flatten (784 numbers) ─► Linear 784→128 ─► ReLU ─► Linear 128→64 ─► ReLU ─► Linear 64→10 ─► 10 scores
                                                                                                  "logits": one per digit
```
1. **`device`** picks the fastest hardware available. `.to(device)` moves the model and each batch there.
2. **`DigitNet`** is the network. `nn.Flatten()` turns the 28×28 image into one row of 784 numbers. Three `nn.Linear` layers (the "neurons" from Level 2) shrink that to 128, 64, then 10 numbers, with `nn.ReLU()` between them (ReLU = "keep positives, turn negatives into 0", which lets the network learn curves, not just straight lines). This is called an **MLP** (multi-layer perceptron). It has 109,386 weights to learn.
3. **`get_data()`** downloads MNIST: 60,000 training images and 10,000 test images of handwritten digits, each 28×28 greyscale. `transforms.ToTensor()` turns each image into a tensor with values 0–1; `Normalize((0.1307,), (0.3081,))` shifts them to roughly mean 0, std 1 (those are MNIST's average and spread), which makes training smoother. In `--smoke` mode it returns random tensors instead.
4. **`DataLoader(train_set, batch_size=64, shuffle=True)`** hands out batches of 64 images. Updating after every 64 images is much faster than after all 60,000, and much steadier than after each single one. `shuffle=True` mixes the order every **epoch** (one full pass through the training images).
5. **The training loop** (the 4 numbered comments in the code):
   1. `loss = loss_fn(model(x), y)`: predict scores for the batch and measure how wrong they are;
   2. `optimizer.zero_grad()`: clear the gradients from the previous batch (PyTorch adds them up otherwise);
   3. `loss.backward()`: backpropagation, the same chain rule as your micrograd in 2.6, done for you;
   4. `optimizer.step()`: nudge every weight downhill. **Adam** is a smarter version of plain gradient descent that adapts the step size per weight. `lr=1e-3` (0.001) is its usual starting learning rate.
6. **`nn.CrossEntropyLoss()`** takes the 10 raw scores (**logits**), turns them into probabilities with softmax, and returns `-log(probability of the right digit)`. Confident and right → near 0. Confident and wrong → large.
7. **`evaluate()`** measures accuracy on the test set. `model.eval()` switches off training-only behaviour (like Dropout, which you'll add in "Try this"), `torch.no_grad()` skips gradient tracking (faster, less memory), and `.argmax(1)` picks the digit with the highest score.
8. **`torch.save(model.state_dict(), "mnist_mlp.pt")`** saves only the learned numbers (a "state dict"), not the code. To load it later you create a `DigitNet()` and call `load_state_dict(...)`, which is exactly what 4.5 does. Smoke runs don't save, so they can never overwrite your real model.
9. **`ascii_digit()`** draws a test image with characters (every second pixel, so it fits your terminal), and `x.unsqueeze(0)` turns one image into a batch of 1, because models always expect batches.

## If something goes wrong
- **`RuntimeError` / `URLError` while downloading MNIST** → you're offline or a firewall blocks the download. Try again on another network; if a half-finished download is stuck, delete the `data/` folder and re-run. `--smoke` works offline.
- **Training is very slow (many minutes per epoch)** → other programs are using the CPU, or PyTorch is fighting itself for CPU cores. Close heavy apps; on Linux/macOS try `OMP_NUM_THREADS=2 python train_mnist.py`. Or use Google Colab with a free GPU.
- **`ModuleNotFoundError: No module named 'torchvision'`** → activate your virtual environment and run `pip install -r requirements.txt`. If pip can't find a torch build for your Python, follow the selector at https://pytorch.org/get-started/locally/.
- **Smoke run accuracy is ~10%** → correct! It trains on random noise. Run without `--smoke` for the real thing.
- **`mnist_mlp.pt` doesn't appear** → you ran with `--smoke` (nothing is saved), or you're looking in a different folder from where you ran the script.

## Try this
1. **Add dropout.** Add `nn.Dropout(0.2)` after each `nn.ReLU()`. Dropout randomly switches off 20% of neurons during training, so the network can't rely on any single one. Does test accuracy change?
   <details><summary>Hint</summary>

   `nn.Linear(28 * 28, 128), nn.ReLU(), nn.Dropout(0.2),` and the same after the second ReLU. Accuracy after 3 epochs moves from 97.08% to about 97.25%: a small gain, because this network barely overfits in 3 epochs. Dropout matters more for bigger networks and longer training. `model.eval()` turns it off for testing automatically.
   </details>
2. **Look for overfitting.** Train for 10 epochs and print *training* accuracy next to test accuracy each epoch. Does the gap grow?
   <details><summary>Solution</summary>

   Change `range(1 if SMOKE else 3)` to `range(1 if SMOKE else 10)` and change the per-epoch print to:
   ```python
   print(f"epoch {epoch + 1} train {evaluate(model, train_loader):.2%} | test {evaluate(model, test_loader):.2%}")
   ```
   Training accuracy keeps climbing (about 96% → 99.4%) while test accuracy flattens out around 97.5–97.9% from epoch 5 on. The growing gap is the network memorising the training images. (`evaluate()` calls `model.eval()`; the next epoch calls `model.train()` again at the top of the loop, so this is safe.)
   </details>
3. **Clothes instead of digits.** Replace both `datasets.MNIST(` with `datasets.FashionMNIST(`: 28×28 pictures of T-shirts, trousers, shoes and bags, in 10 classes. Nothing else needs to change.
   <details><summary>Hint</summary>

   It downloads ~30 MB. Test accuracy lands around 84–86% (and wobbles from epoch to epoch) instead of 97%: clothes are harder than digits, because a shirt and a pullover look alike when flattened into 784 numbers. The ASCII art now shows a piece of clothing, and the "digit" number is a class index (0 = T-shirt, 9 = ankle boot). You'll beat this with a CNN in 4.2.
   </details>

## Check yourself
1. What does one epoch mean, and how many batches of 64 are in one epoch of MNIST's 60,000 training images?
2. Why do we call `optimizer.zero_grad()` every batch?
3. Why does the loss start at about 2.3?
4. What does `model.eval()` + `torch.no_grad()` do, and when do you use them?

<details><summary>Answers</summary>

1. One full pass through all training images. 60,000 / 64 = 937.5, so 938 batches (the last one is smaller). That's why the printed batch numbers stop at 900.
2. PyTorch *adds* new gradients to old ones. Without clearing them, each update would also include all previous batches' gradients and training would go wrong.
3. At the start the network gives every digit roughly equal probability, 1/10. The loss is −log(1/10) = ln 10 ≈ 2.30.
4. `eval()` switches layers like Dropout and BatchNorm to testing behaviour; `no_grad()` stops PyTorch recording operations for backprop, saving time and memory. Use them whenever you're testing or predicting, not training.
</details>

## Learn more (optional)
- But what is a neural network? (3Blue1Brown, uses MNIST as its example): https://www.youtube.com/results?search_query=3blue1brown+but+what+is+a+neural+network
- PyTorch quickstart (also MNIST-style): https://pytorch.org/tutorials/beginner/basics/quickstart_tutorial.html
- PyTorch Datasets & DataLoaders: https://pytorch.org/tutorials/beginner/basics/data_tutorial.html

## Next
→ [4.2 · Cats vs dogs: a Convolutional Neural Network](../02-cats-vs-dogs-cnn)
