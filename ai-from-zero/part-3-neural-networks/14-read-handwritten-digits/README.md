# 14 · Read handwritten digits

**What you'll build:** a neural network that learns from 60,000 handwritten numbers and then reads digits it has **never seen** about 97% of the time. It saves its "brain" to a file for the next project.
**Time:** ~1 hour · **Builds on:** [13 · Same brain in PyTorch](../13-same-brain-in-pytorch) · **Needs:** `torch`, `torchvision`, internet for a one-time 12 MB download

## Why this matters
Reading handwriting was one of the first big wins for neural networks: banks used it to read cheques and post offices to read postcodes. More importantly, this is the full real-world recipe: a big labelled dataset, training in batches, testing on data the model never saw, and saving the trained model to use somewhere else. Image, speech and text models are all trained this way.

## What you'll learn
- **Dataset (MNIST):** 70,000 small 28×28 pictures of handwritten digits, each with the correct answer (its **label**).
- **Training set vs test set:** learn from 60,000 pictures, then take an exam on 10,000 *different* pictures to prove it can handle new ones.
- **Batches and epochs ("laps"):** learn from 64 pictures at a time; one lap = one pass through all 60,000.
- **Classification with 10 scores:** the network gives one score per digit and its answer is the highest score.
- **Saving a model:** `torch.save` writes the learned knobs to a file so you don't have to retrain.

## Before you start
- Install, with your virtual environment on:
  ```bash
  pip install torch torchvision
  ```
  `torch` is PyTorch; `torchvision` downloads the MNIST pictures and turns them into numbers. Or install everything for Part 3: `pip install numpy torch torchvision pillow fastapi "uvicorn[standard]"`
- You need internet the first time (it downloads about 12 MB into a `data` folder here).
- No API key and no graphics card needed.

## Run it
1. Open a terminal in the `ai-from-zero` folder.
2. Run:
   ```bash
   cd part-3-neural-networks/14-read-handwritten-digits
   python read_digits.py
   ```
3. Wait. It prints a download bar, then "Training...", then one line per lap. On a normal laptop the whole thing takes a few minutes (slow computers can take 10).

### What you should see
```
100%|██████████| 9.91M/9.91M [00:00<00:00, 25.7MB/s]
...(three more small download bars)...
Training... each lap can take a minute or more, so be patient.
lap 1: 94.9% of unseen digits read correctly
lap 2: 96.1% of unseen digits read correctly
lap 3: 97.0% of unseen digits read correctly
Saved digit_brain.pt (project 15 uses it)
              
              
              
              
   ████████   
          █   
         █    
         █    
        █     
        █     
       █      
      █       
      █       
      █       
Model says: 7   (true answer: 7)
```
Your percentages will be slightly different (the pictures are shuffled randomly), but you should get about 97% after 3 laps. The text picture is the first test image drawn with `█` blocks, plus the model's answer. You now have a file called `digit_brain.pt` in this folder.

## How it works
1. **Turn pictures into numbers.** `transforms.ToTensor()` turns each 28×28 picture into a grid of 784 numbers from 0 (black) to 1 (white).
2. **Load the data.** `datasets.MNIST("data", train=True, download=True, ...)` downloads the 60,000 training pictures into `data/` (only the first time). `train=False` gives the 10,000 test pictures.
3. **Batches.** `DataLoader(train_data, batch_size=64, shuffle=True)` serves the training pictures 64 at a time, in a new random order each lap. Learning from small batches is faster than one picture at a time, and shuffling stops it learning the order.
4. **The brain.**
   ```
   28×28 picture → Flatten → 784 numbers → Linear(784, 128) → ReLU → Linear(128, 10) → 10 scores
   ```
   - `Flatten()` lays the 28 rows end to end into one row of 784 numbers.
   - `Linear(784, 128)` + `ReLU()`: 128 hidden neurons. `ReLU` is a simpler squash than sigmoid: negative numbers become 0, positives pass through. It trains faster on big networks.
   - `Linear(128, 10)`: 10 scores, one for each digit 0–9.
5. **Loss and optimizer.** `CrossEntropyLoss()` is the standard loss for "pick one of several answers": it's small when the right digit has by far the highest score. `Adam(..., lr=0.001)` is the optimizer from project 13's Try this.
6. **Training.** For each of 3 laps (`range(1, 4)`), and each batch of 64: the same 4-line loop as project 13 (measure, `zero_grad`, `backward`, `step`).
7. **The exam.** After each lap, `torch.no_grad()` says "no learning now, just answer". It runs all 10,000 test pictures through the brain, `argmax(dim=1)` picks the highest score for each, and `score` is the fraction it got right. These pictures were never used for training, so this is an honest measure.
8. **Save.** `torch.save(brain.state_dict(), "digit_brain.pt")` writes all the knob values (about 100,000 of them) to a small file.
9. **Show one.** It draws test picture 0 as text (every second pixel, so it fits) and prints the model's answer.

## If something goes wrong
- **`ModuleNotFoundError: No module named 'torchvision'`** → turn on your virtual environment and run `pip install torch torchvision`.
- **Download error (`HTTP Error 403`, `URLError`, or it hangs)** → check your internet, then run it again. torchvision tries several mirrors. Company or school networks sometimes block downloads; try another network.
- **It seems frozen after "Training..."** → it's working. Each lap processes 60,000 pictures. Give it a few minutes before worrying.
- **`RuntimeError: ... invalid ... file` or a broken download** → delete the `data` folder in this project and run again to re-download.
- **Accuracy stuck around 10%** → it's guessing randomly, so something in the loop changed. Compare your 4 training lines with the original (`zero_grad`, `backward`, `step` must all be there).

## Try this
1. **More laps.** Change `range(1, 4)` to `range(1, 6)` (5 laps). Does the score keep rising?
   <details><summary>Hint</summary>

   It creeps up a little (one test run went 94.5% → 96.5% → 97.3% → 97.3% → 97.7%) and then levels off. More laps don't help forever, and too many can make a model memorise its training pictures instead of learning digits (called **overfitting**).
   </details>
2. **Learn clothes instead.** Change `datasets.MNIST` to `datasets.FashionMNIST` on **both** lines. Same code, new skill: shirts, shoes, bags.
   <details><summary>Hint</summary>

   Expect about 85% after 3 laps (the message still says "digits", but it means clothes now): clothes are harder than digits. It still saves to `digit_brain.pt`, so re-run the original MNIST version before project 15, or change the file name.
   </details>
3. **Find its mistakes.** After running the main script once, make a new file `mistakes.py` in this folder that loads `digit_brain.pt`, counts how many test pictures it gets wrong, and draws one of them.
   <details><summary>Solution</summary>

   ```python
   import torch
   from torchvision import datasets, transforms

   test_data = datasets.MNIST("data", train=False, download=True, transform=transforms.ToTensor())
   brain = torch.nn.Sequential(torch.nn.Flatten(), torch.nn.Linear(784, 128), torch.nn.ReLU(), torch.nn.Linear(128, 10))
   brain.load_state_dict(torch.load("digit_brain.pt", weights_only=True))

   with torch.no_grad():
       guesses = brain(test_data.data.float().unsqueeze(1) / 255).argmax(dim=1)
   wrong = (guesses != test_data.targets).nonzero().flatten()     # positions of the wrong answers
   print(f"{len(wrong)} wrong out of {len(test_data)}")

   i = wrong[0].item()
   picture, label = test_data[i]
   for row in picture[0][::2]:
       print("".join("█" if pixel > 0.5 else " " for pixel in row[::2]))
   print(f"Model said {guesses[i].item()}, the true answer is {label}")
   ```
   You'll see around 300 wrong, and many of them are digits a human would find tricky too.
   </details>

## Check yourself
1. Why test on 10,000 pictures the model never trained on, instead of the training pictures?
2. How does the network turn its output into one answer?
3. What is one "lap" (epoch), and what is a batch?
4. What exactly is inside `digit_brain.pt`?

<details><summary>Answers</summary>

1. A model can simply memorise its training pictures. Only new pictures show whether it really learned to read digits.
2. It outputs 10 scores, one per digit, and `argmax` picks the digit with the highest score.
3. One lap is one pass through all 60,000 training pictures. A batch is the 64 pictures it learns from in one nudge.
4. The learned knob values (weights and biases) of every layer. Not the code and not the pictures, which is why project 15 has to build the same layers before loading it.
</details>

## Learn more (optional)
- 3Blue1Brown, "But what is a neural network?" (uses this exact digit example): https://www.youtube.com/results?search_query=3blue1brown+but+what+is+a+neural+network
- The MNIST dataset explained: https://www.youtube.com/results?search_query=mnist+dataset+explained

## Next
→ [15 · Draw-a-digit app](../15-draw-a-digit-app)
