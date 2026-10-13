# 4.3 · Transfer learning: a pretrained ResNet on your own photos

**What you build:** a classifier for **your own** categories (fruits, your pets, Lego vs. Duplo, ripe vs. unripe tomatoes...) from just **30–100 photos per class**. You borrow ResNet-18, already trained on 1.2 million photos, and only teach it the final step.
**Like you're 10:** a professional chef already knows knives, heat and taste. Teaching them *your* grandma's recipe takes an afternoon, not 10 years of cooking school. That's transfer learning.

## Step 1: get photos
**Option A, your own (most fun):** take ~40 phone photos per class and arrange them like this:
```
dataset/
  train/  apple/ banana/ orange/     ← ~80% of photos
  val/    apple/ banana/ orange/     ← ~20% of photos (different photos!)
```
**Option B, demo dataset:** `python make_demo_dataset.py` builds airplane / car / ship folders from CIFAR-10.

## Step 2: train and predict
```bash
cd level-4-computer-vision/03-transfer-learning-resnet-on-your-own-photos
pip install -r requirements.txt
python train_transfer.py --smoke      # wiring check (no downloads)
python train_transfer.py              # downloads ResNet-18 weights (~45 MB) once, trains 5 epochs
python predict.py dataset/val/apple/some_photo.jpg
```
Expect 90%+ validation accuracy within a few epochs, even on CPU.

## Key ideas
- **Pretrained backbone:** ResNet's early layers already detect edges, textures and shapes. Those skills transfer to almost any photo.
- **Freezing:** `requires_grad = False` locks those 11M weights. Only the new final layer (~1.5K weights) trains, so it's fast and needs little data.
- **Same preprocessing as pretraining:** 224×224 and ImageNet mean/std normalisation. Get this wrong and accuracy collapses.
- **`ImageFolder`:** folder names become labels automatically.
- **Fine-tuning (next step up):** after the head trains, unfreeze the last block (`model.layer4`) with a tiny learning rate (1e-4) for extra accuracy.

## Your turn
1. Implement the fine-tuning step above and compare accuracy.
2. Try `models.efficientnet_b0` or `models.mobilenet_v3_small` (great for phones).
3. Print a confusion matrix on the val set. Which classes get mixed up, and why?

## Watch
- Transfer learning tutorial (official PyTorch): https://pytorch.org/tutorials/beginner/transfer_learning_tutorial.html
- Transfer learning explained: https://www.youtube.com/results?search_query=transfer+learning+explained+deep+learning
