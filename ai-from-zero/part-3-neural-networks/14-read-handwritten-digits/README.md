# 14 · Read handwritten digits

**What it does:** trains a neural network on 60,000 handwritten numbers. After 3 laps it reads digits it has **never seen** about 97% of the time. It saves its "brain" to a file for the next project.

## Run it
```bash
cd part-3-neural-networks/14-read-handwritten-digits
python read_digits.py
```
You'll see the score after each lap, then a digit drawn in text with the model's answer.

## The idea in one sentence
Exactly the loop from project 13, just with pictures: each picture becomes 784 numbers (one per pixel), and the network outputs 10 scores (one per digit) and picks the highest.

## Try this
1. Change `range(1, 4)` to `range(1, 6)` (5 laps). Does the score keep rising?
2. Swap `datasets.MNIST` for `datasets.FashionMNIST` (both lines). Now it learns clothes (shirts, shoes, bags) with the same code!
