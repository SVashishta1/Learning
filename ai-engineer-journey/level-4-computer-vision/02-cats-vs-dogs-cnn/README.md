# 4.2 · Cats vs dogs: a Convolutional Neural Network

**What you build:** a CNN that tells cats from dogs in small 32×32 photos (the cat and dog classes of CIFAR-10). Expect around **80–85%** accuracy after ~10 epochs. That's harder than it sounds at this tiny resolution!
**Like you're 10:** instead of staring at the whole picture at once, the CNN looks through a **small magnifying glass** that slides across the image. First it spots lines and corners, then shapes made of lines (eyes, ears), then "that's a pointy-eared furry face → cat!"

## Run it
```bash
cd level-4-computer-vision/02-cats-vs-dogs-cnn
pip install -r requirements.txt
python train_cnn.py --smoke     # wiring check
python train_cnn.py             # downloads CIFAR-10 (~170 MB) and trains (~5-15 min on CPU)
```

## Key ideas
- **Convolution:** a 3×3 filter of learnable weights slides over the image. The same filter is used everywhere, so a "whisker detector" works anywhere in the photo. That makes CNNs far more efficient than the flat network from 4.1.
- **Pooling (`MaxPool2d`):** shrinks the image and keeps the strongest signals.
- **Data augmentation:** random flips and crops create "new" training photos for free, which reduces overfitting.
- **BatchNorm, Dropout, AdamW, OneCycleLR:** standard tricks for stable, fast training. Try removing each one and compare.

## Your turn
1. Remove the augmentation lines. How do train loss and test accuracy compare now? (Classic overfitting.)
2. Train on all 10 CIFAR-10 classes (change the final layer to 10 outputs).
3. Use the **real** Kaggle Dogs vs. Cats dataset (bigger photos): resize to 128×128 and add one more `block`.

## Watch
- But what is a convolution? (3Blue1Brown): https://www.youtube.com/results?search_query=3blue1brown+but+what+is+a+convolution
- CNNs explained (StatQuest): https://www.youtube.com/results?search_query=statquest+neural+networks+part+8+image+classification+convolutional
- CS231n CNN notes: https://cs231n.github.io/convolutional-networks/
