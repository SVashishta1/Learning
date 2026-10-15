# 4.2 · Cats vs dogs: a Convolutional Neural Network

**What you'll build:** a CNN that tells cats from dogs in small 32×32 colour photos (the cat and dog classes of CIFAR-10). Expect around **80–85%** test accuracy after 10 epochs. That's harder than it sounds at this tiny resolution!
**Like you're 10:** instead of staring at the whole picture at once, the CNN looks through a **small magnifying glass** that slides across the image. First it spots lines and corners, then shapes made of lines (eyes, ears), then "that's a pointy-eared furry face → cat!"
**Time:** ~2 h · **Builds on:** [4.1 MNIST digits](../01-mnist-digits-simple-neural-net) · **Needs:** nothing extra (GPU optional; internet once for the ~170 MB dataset)

## Why this matters
Convolutional neural networks are how computers learned to see. The same building blocks (convolution, pooling, BatchNorm, augmentation) are inside photo apps, medical-scan readers, self-checkout cameras and factory quality control. Even when you use a big pretrained model (4.3), knowing what's inside lets you choose, debug and fine-tune it.

## What you'll learn
- **Convolution**: a small grid of learnable weights (a *filter*) that slides over the image looking for one pattern.
- **Pooling**: shrinking the image while keeping the strongest signals.
- **Data augmentation**: random flips and crops that create "new" training photos for free and reduce overfitting.
- **Training helpers**: BatchNorm, Dropout, AdamW and a OneCycle learning-rate schedule, the standard tricks for stable, fast training.

## Before you start
```bash
pip install -r requirements.txt
```
- `torch`: the network, loss, optimizer and training loop.
- `torchvision`: downloads CIFAR-10 and provides the image transforms (flip, crop, normalise).

No API key needed. The first real run downloads CIFAR-10 (~170 MB) into `data/`. A GPU makes it much faster but isn't required.

## Run it
1. From the course root:
   ```bash
   cd level-4-computer-vision/02-cats-vs-dogs-cnn
   pip install -r requirements.txt
   ```
2. Wiring check (a few seconds, random fake images, no download, nothing saved):
   ```bash
   python train_cnn.py --smoke
   ```
3. Train for real (downloads CIFAR-10, ~5–15 min on a laptop CPU, ~1 min on a GPU; saves `cat_dog_cnn.pt`):
   ```bash
   python train_cnn.py
   ```

### What you should see
The smoke run (real output):
```
256 training images | device cpu | 292,002 parameters
epoch  1 | train loss 1.320 | test accuracy 45.3%
smoke run: not saving (a model trained on random noise would overwrite your real one)
```
A real run looks like this (CIFAR-10 couldn't be downloaded where this lesson was checked, so this is an example; your exact numbers will differ):
```
10000 training images | device cpu | 292,002 parameters
epoch  1 | train loss 0.640 | test accuracy 66.9%
epoch  2 | train loss 0.560 | test accuracy 71.5%
epoch  3 | train loss 0.517 | test accuracy 74.0%
...
epoch  9 | train loss 0.352 | test accuracy 83.6%
epoch 10 | train loss 0.330 | test accuracy 84.1%
saved cat_dog_cnn.pt
```
What to look at:
- **10,000 training images**: CIFAR-10's 5,000 cats + 5,000 dogs. The test set has 2,000 (1,000 of each).
- **Train loss goes down every epoch, test accuracy goes up.** Random guessing would be 50% and a loss of 0.69.
- **Test accuracy keeps improving until the end**, thanks to augmentation and the learning-rate schedule. Without them, test accuracy stalls early while train loss keeps falling (try it in "Try this").

## How it works
```
photo 3×32×32 ─► block(3→32) ─► 32×16×16 ─► block(32→64) ─► 64×8×8 ─► block(64→128) ─► 128×4×4
                                                                                            │
                                         2 scores (cat, dog) ◄─ Linear ◄─ Dropout ◄─ Flatten (2,048 numbers)
```
1. **`CatDogCNN`** is built from three `block`s. Each block is two **convolution** layers then a **pooling** layer:
   - `nn.Conv2d(c_in, c_out, 3, padding=1)` slides `c_out` different 3×3 filters over the image. Each filter is a little pattern detector (an edge at some angle, a colour blob…), and its output is a "map" of where that pattern appears. The same 3×3 weights are reused at every position, so a "whisker detector" works anywhere in the photo with very few weights. That's why a CNN needs far fewer weights than 4.1's flat network would for colour photos. `padding=1` adds a 1-pixel border so the size stays 32×32.
   - `nn.BatchNorm2d` re-centres each layer's outputs to a steady range, which makes training faster and more stable.
   - `nn.ReLU()` keeps positives, zeros negatives (as in 4.1).
   - `nn.MaxPool2d(2)` keeps the biggest value in each 2×2 square, halving width and height (32→16→8→4). The image gets smaller, but the number of channels (32→64→128) grows: fewer *where*, more *what*. Early blocks see edges; later blocks, whose filters look at the earlier maps, see ears, eyes and fur.
2. **`classifier`** flattens the final 128×4×4 maps into 2,048 numbers, applies `nn.Dropout(0.3)` (randomly zero 30% of them while training, so the model can't rely on one feature), and a `nn.Linear` gives 2 scores: cat and dog.
3. **`cats_and_dogs(train)`** downloads CIFAR-10 (60,000 tiny photos in 10 classes), keeps only class 3 (cat) and 5 (dog) using a `Subset`, and relabels them 0 = cat, 1 = dog.
   - **Augmentation** (training only): `RandomHorizontalFlip()` mirrors half the photos; `RandomCrop(32, padding=4)` pads by 4 pixels and cuts a random 32×32 window, shifting the animal around a bit. A flipped cat is still a cat, so the model sees a slightly different version of each photo every epoch and can't simply memorise them.
   - `Normalize(...)` shifts each colour channel to roughly mean 0, std 1 (as in 4.1, but per red/green/blue).
4. **Optimizer and schedule.** `AdamW` is Adam with *weight decay* (a gentle pull of all weights towards 0, which reduces overfitting). `OneCycleLR` changes the learning rate after every batch: it warms up from small to `max_lr=2e-3`, then slowly cools to almost 0, so training is fast in the middle and careful at the end. That's why `scheduler.step()` is called inside the batch loop.
5. **The loop** is 4.1's loop: forward → loss → `zero_grad` → `backward` → `step`. After each epoch, `model.eval()` + `torch.no_grad()` measure test accuracy (in eval mode, Dropout is off and BatchNorm uses its learned averages).
6. **`torch.save(model.state_dict(), "cat_dog_cnn.pt")`** saves the weights (smoke runs skip this).

## If something goes wrong
- **Download fails or is very slow** (`URLError`, `ConnectionResetError`) → CIFAR-10 is 170 MB from the University of Toronto. Try another network or try later. If a broken download is stuck, delete the `data/` folder. `--smoke` works offline.
- **Training takes far longer than 15 minutes** → your CPU is busy or slow. Close other apps; on Linux/macOS try `OMP_NUM_THREADS=2 python train_cnn.py`. Or run it on Google Colab with a free GPU (*Runtime → Change runtime type → T4 GPU*).
- **`RuntimeError: mat1 and mat2 shapes cannot be multiplied`** (after you changed the network) → the `nn.Linear(128 * 4 * 4, 2)` input size must match what comes out of the last block. Each block halves the image size; update the numbers if you add or remove a block or change the image size.
- **Smoke accuracy is around 50%** → expected: random labels on random images. Only the real run is meaningful.
- **`RuntimeError: MPS backend out of memory` / CUDA out of memory** → lower `batch_size=64` to 32.

## Try this
1. **Remove augmentation.** In `cats_and_dogs()`, replace the augmentation list with `[]` so training photos are never flipped or cropped. Compare train loss and test accuracy with your earlier run.
   <details><summary>Hint</summary>

   Change `([transforms.RandomHorizontalFlip(), transforms.RandomCrop(32, padding=4)] if train else [])` to `[]`. Train loss falls much lower (the model memorises the 10,000 photos) but test accuracy peaks early and ends lower. Low train loss + worse test accuracy = classic overfitting.
   </details>
2. **All 10 classes.** Train on all of CIFAR-10 (planes, cars, birds, cats, deer, dogs, frogs, horses, ships, trucks).
   <details><summary>Solution</summary>

   - In `CatDogCNN`, change `nn.Linear(128 * 4 * 4, 2)` to `nn.Linear(128 * 4 * 4, 10)`.
   - In `cats_and_dogs()`, replace the last three lines with `return ds` (keep every photo and the original 0–9 labels).
   - In the smoke data, change `torch.randint(0, 2, ...)` to `torch.randint(0, 10, ...)`.

   You now train on 50,000 photos (5× slower per epoch). Expect around 85–88% after 10 epochs. Random guessing would be 10%.
   </details>
3. **Bigger photos.** Use the real Kaggle "Dogs vs. Cats" photos (search for it on kaggle.com; free account needed), resized to 128×128.
   <details><summary>Hint</summary>

   Put the photos in `catsdogs/train/cat`, `catsdogs/train/dog`, `catsdogs/test/cat`, `catsdogs/test/dog` and load them with `torchvision.datasets.ImageFolder("catsdogs/train", transform=tf)` (folder names become labels, as you'll see in 4.3). Add `transforms.Resize((128, 128))` at the start of `tf`. Add a fourth block, `block(128, 256)`: 128→64→32→16→8 pixels, so the Linear layer becomes `nn.Linear(256 * 8 * 8, 2)`. Expect 90%+ with enough epochs, and a much slower epoch on CPU.
   </details>

## Check yourself
1. Why does a convolution layer need far fewer weights than a Linear layer looking at the whole image?
2. What does `MaxPool2d(2)` do to a 32×32 feature map, and why is that useful?
3. Why do we only augment the *training* images, never the test images?
4. Train loss keeps dropping but test accuracy got worse over the last few epochs. What's happening, and name two fixes from this lesson.

<details><summary>Answers</summary>

1. A 3×3 filter has only 9 weights per input channel, and the same weights are reused at every position in the image. A Linear layer needs a separate weight for every pixel-to-neuron connection.
2. It keeps the largest value in each 2×2 square, giving a 16×16 map. It reduces computation, keeps the strongest signals, and makes the next layer's 3×3 filters "see" a larger area of the original photo.
3. Augmentation is a training trick to show more variety. The test set must stay fixed and realistic so the score is comparable and honest.
4. Overfitting: the model is memorising training photos. Fixes: data augmentation, Dropout, weight decay (AdamW), or stopping training earlier.
</details>

## Learn more (optional)
- But what is a convolution? (3Blue1Brown): https://www.youtube.com/results?search_query=3blue1brown+but+what+is+a+convolution
- CNNs explained (StatQuest): https://www.youtube.com/results?search_query=statquest+neural+networks+part+8+image+classification+convolutional
- CS231n CNN notes (Stanford): https://cs231n.github.io/convolutional-networks/
- CNN Explainer (interactive, in your browser): https://poloclub.github.io/cnn-explainer/

## Next
→ [4.3 · Transfer learning: a pretrained ResNet on your own photos](../03-transfer-learning-resnet-on-your-own-photos)
