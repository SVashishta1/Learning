# 4.3 · Transfer learning: a pretrained ResNet on your own photos

**What you'll build:** a classifier for **your own** categories (fruits, your pets, Lego vs. Duplo, ripe vs. unripe tomatoes...) from just **30–100 photos per class**. You borrow ResNet-18, already trained on 1.2 million photos, and only teach it the final step. Then you classify any photo with `predict.py`.
**Like you're 10:** a professional chef already knows knives, heat and taste. Teaching them *your* grandma's recipe takes an afternoon, not 10 years of cooking school. That's transfer learning.
**Time:** ~2 h · **Builds on:** [4.2 Cats vs dogs CNN](../02-cats-vs-dogs-cnn) · **Needs:** internet once (ResNet weights ~45 MB, plus ~170 MB if you use the demo dataset); GPU optional

## Why this matters
Almost nobody trains vision models from scratch at work. You take a model pretrained on millions of images and adapt it to your problem with a small dataset: spotting defects on a production line, sorting recycling, identifying plant diseases from a phone photo. Transfer learning is the reason a small team with 200 photos can ship a useful image classifier in a day. The same idea powers fine-tuning LLMs in Level 6.

## What you'll learn
- **Pretrained backbone**: ResNet's early layers already detect edges, textures and shapes, and those skills transfer to almost any photo.
- **Freezing**: locking the 11 million pretrained weights so only a tiny new final layer learns your classes.
- **Matching preprocessing**: 224×224 images normalised with ImageNet's mean and std, exactly as during pretraining.
- **`ImageFolder`**: folder names automatically become class labels.
- **Saving a model with its labels**: a checkpoint that a separate script (or the API in 4.4) can load and use.

## Before you start
```bash
pip install -r requirements.txt
```
- `torch`: the network and training loop.
- `torchvision`: the pretrained ResNet-18, `ImageFolder`, image transforms, and CIFAR-10 for the demo dataset.
- `pillow`: opens your photos (JPG, PNG...).

No API key needed. The first real training run downloads the ResNet-18 weights (~45 MB) from pytorch.org and caches them (in `~/.cache/torch`), so later runs work offline.

## Run it
1. From the course root:
   ```bash
   cd level-4-computer-vision/03-transfer-learning-resnet-on-your-own-photos
   pip install -r requirements.txt
   ```
2. **Get photos.** Choose one option:
   - **Option A, your own photos (most fun).** Take ~40 phone photos per class (2–5 classes) and arrange them like this. Folder names become class names:
     ```
     dataset/
       train/  apple/ banana/ orange/     ← ~80% of photos
       val/    apple/ banana/ orange/     ← ~20% of photos (different photos!)
     ```
   - **Option B, demo dataset.** Build airplane / car / ship folders from CIFAR-10 (downloads ~170 MB, writes 450 training and 150 validation pictures):
     ```bash
     python make_demo_dataset.py
     ```
3. Wiring check (random weights, fake images, no downloads, nothing saved):
   ```bash
   python train_transfer.py --smoke
   ```
4. Train for real (downloads ResNet-18 weights once, trains 5 epochs, saves `transfer_model.pt`):
   ```bash
   python train_transfer.py
   ```
5. Classify one photo (any image file works):
   ```bash
   python predict.py dataset/val/car/3.jpg
   ```

### What you should see
The smoke run (real output):
```
classes: ['apple', 'banana', 'cherry']
trainable parameters: 1,539 of 11,178,051
epoch 1 | last batch loss 2.166 | val accuracy 37.5%
smoke run: not saving (random weights would overwrite your real model)
```
A real run on the demo dataset looks like this (the pretrained weights and CIFAR-10 couldn't be downloaded where this lesson was checked, so this is an example; your numbers will differ):
```
classes: ['airplane', 'car', 'ship']
trainable parameters: 1,539 of 11,178,051
epoch 1 | last batch loss 0.512 | val accuracy 84.7%
epoch 2 | last batch loss 0.394 | val accuracy 88.0%
epoch 3 | last batch loss 0.433 | val accuracy 89.3%
epoch 4 | last batch loss 0.251 | val accuracy 90.7%
epoch 5 | last batch loss 0.302 | val accuracy 91.3%
saved transfer_model.pt (copy it to project 4.4 to serve it)
```
and `predict.py`:
```
car             96.2%
ship             2.9%
airplane         0.9%
```
What to look at:
- **1,539 of 11,178,051 parameters train**: only the new last layer (512 inputs × 3 classes + 3). Everything else is frozen.
- **High accuracy after the very first epoch.** A CNN from scratch (4.2) needed 10 epochs and 10,000 photos to reach ~84%. Here 150 photos per class are enough, because the "seeing" was already learned. (The demo pictures are blurry 32×32 photos blown up to 224×224, so your own sharp phone photos usually do even better.)

## How it works
```
your photo ─► eval_transform (resize 256, crop 224, normalise) ─► ResNet-18 body (frozen) ─► 512 numbers ─► new Linear ─► your classes
                                                                  "what's in this picture"                  "which of MY classes?"
```
1. **`common.py`** holds everything that training *and* serving must agree on (it's copied into 4.4 for that reason):
   - `eval_transform`: resize to 256, cut out the centre 224×224, convert to a tensor, normalise with `IMAGENET_MEAN`/`IMAGENET_STD`. ResNet was trained on images prepared exactly like this; feed it anything else and accuracy collapses.
   - `train_transform`: the training version with augmentation (random crop of 70–100% of the photo, random flip, small colour changes), as in 4.2.
   - `build_model(num_classes)`: loads ResNet-18 with its ImageNet weights (`ResNet18_Weights.DEFAULT`), sets `requires_grad = False` on every parameter (**freezing**: the optimizer can't change them), then replaces the final layer `model.fc` (which used to score ImageNet's 1,000 classes) with a fresh `nn.Linear(512, num_classes)`. New layers are trainable by default.
   - `load_checkpoint(path)`: rebuilds the same model shape (no download needed: `pretrained=False`, the saved weights replace everything) and loads the saved weights and class names.
2. **`make_demo_dataset.py`** loops through CIFAR-10, keeps the first 150 (train) / 50 (val) airplanes, cars and ships, resizes them to 224×224 and saves them as JPGs in the same folder layout you'd use for your own photos.
3. **`train_transfer.py`:**
   - `ImageFolder("dataset/train", transform=train_transform)` finds every image in the class sub-folders; the folder names (sorted alphabetically) become `classes` and labels 0, 1, 2…
   - The optimizer only gets the parameters with `requires_grad`, i.e. the new head.
   - **Why `model.eval()` during training?** Normally you'd call `model.train()`. But ResNet contains BatchNorm layers, and in train mode they keep updating their ImageNet averages using your few photos, even when frozen, which quietly hurts accuracy. The only layer learning is the Linear head, which behaves the same in both modes, so the whole model stays in eval mode.
   - After each epoch it prints the last batch's loss and the validation accuracy.
   - `torch.save({"state_dict": ..., "classes": classes}, "transfer_model.pt")` stores the weights **and** the class names. The model itself only outputs numbers (0, 1, 2); without the names, nobody knows that 1 means "car".
4. **`predict.py`** loads the checkpoint, opens your photo with Pillow (`.convert("RGB")` handles greyscale and transparent PNGs), applies `eval_transform`, runs the model under `torch.no_grad()`, turns scores into probabilities with `softmax`, and prints the top 3.

## If something goes wrong
- **`FileNotFoundError: ... dataset/train`** → you haven't created the photo folders yet. Do step 2 (your own photos or `python make_demo_dataset.py`), and run the scripts from this folder.
- **`FileNotFoundError: Couldn't find any class folder` / `Found no valid file`** → each class needs its own sub-folder with images inside, in both `train/` and `val/`, with the same class names. Supported types include .jpg, .jpeg and .png.
- **Download of `resnet18-....pth` fails** → you need internet the first time. Once downloaded it's cached in `~/.cache/torch/hub/checkpoints/`.
- **Validation accuracy stuck near random (e.g. 33% for 3 classes)** → check that the val photos are in the right folders, that you didn't run with `--smoke`, and that each class has at least ~20 training photos.
- **`predict.py` says `No such file or directory: 'transfer_model.pt'`** → train first (step 4) in this same folder.

## Try this
1. **Fine-tune the last block.** After the head works, let ResNet's last block (`model.layer4`) learn too, with a tiny learning rate. Compare validation accuracy.
   <details><summary>Solution</summary>

   In `train_transfer.py`, replace the `optimizer = ...` line with:
   ```python
   for p in model.layer4.parameters():
       p.requires_grad = True                                # unfreeze the last block
   optimizer = torch.optim.Adam([
       {"params": model.fc.parameters(), "lr": 1e-3},
       {"params": model.layer4.parameters(), "lr": 1e-4},    # tiny steps: refine, don't wreck
   ])
   ```
   About 8.4 million weights now train, so each epoch is slower. On your own photos this usually adds a few percent. Watch for overfitting if you have very few photos.
   </details>
2. **A phone-sized model.** Swap ResNet-18 for `models.mobilenet_v3_small` (about 2.5M parameters, built for phones).
   <details><summary>Hint</summary>

   In `common.py` → `build_model`:
   ```python
   weights = models.MobileNet_V3_Small_Weights.DEFAULT if pretrained else None
   model = models.mobilenet_v3_small(weights=weights)
   for p in model.parameters():
       p.requires_grad = False
   model.classifier[-1] = nn.Linear(model.classifier[-1].in_features, num_classes)
   ```
   MobileNet's last layer lives in `model.classifier[-1]`, not `model.fc`. Also copy the new `common.py` into 4.4 if you serve it. `models.efficientnet_b0` works the same way (`EfficientNet_B0_Weights`).
   </details>
3. **Where does it get confused?** Print a confusion matrix on the validation set (rows = true class, columns = predicted).
   <details><summary>Solution</summary>

   Add at the end of `train_transfer.py`:
   ```python
   from collections import Counter
   pairs = Counter()
   with torch.no_grad():
       for x, y in val_loader:
           for t, p in zip(y.tolist(), model(x.to(device)).argmax(1).cpu().tolist()):
               pairs[(classes[t], classes[p])] += 1
   print("rows = truth, columns = predicted:", classes)
   for t in classes:
       print(f"{t:>10s}", [pairs[(t, p)] for p in classes])
   ```
   The diagonal holds the correct answers. On the demo dataset, airplanes and ships are the pair most likely to be confused: both are often a grey shape on a blue background (sky or sea).
   </details>

## Check yourself
1. Why can transfer learning work with only ~40 photos per class when 4.2 needed 10,000?
2. What does setting `requires_grad = False` do, and why do we do it here?
3. What would happen if `predict.py` skipped the ImageNet normalisation?
4. Why does the checkpoint store the class names next to the weights?

<details><summary>Answers</summary>

1. The frozen body already knows how to turn any photo into 512 useful numbers (edges, textures, shapes, object parts) from 1.2 million ImageNet photos. Only a small final layer has to learn, and that needs little data.
2. It tells PyTorch not to compute gradients for those weights, so the optimizer never changes them. It keeps the general seeing skills intact, trains much faster, and avoids overfitting a huge model on a few photos.
3. The model would get numbers in a different range from what it was trained on, so its features would be off and predictions would be poor or random. Training and prediction must use identical preprocessing.
4. The model only outputs class indices (0, 1, 2). The names come from your folder names at training time; saving them together means any script can turn "1" back into "car".
</details>

## Learn more (optional)
- Transfer learning tutorial (official PyTorch): https://pytorch.org/tutorials/beginner/transfer_learning_tutorial.html
- Transfer learning explained: https://www.youtube.com/results?search_query=transfer+learning+explained+deep+learning
- ResNet, the paper idea in plain words: https://www.youtube.com/results?search_query=resnet+explained+residual+connections

## Next
→ [4.4 · Serve it: an image classifier behind `/predict`](../04-serve-image-classifier-fastapi)
