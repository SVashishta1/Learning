# 5.2 · Next-letter predictor: a bigram name generator

**What you'll build:** a model that reads 32,000 real names, learns which letter tends to follow which, and **invents new names**. It's the simplest possible *language model*, and the great-grandparent of GPT.
**Like you're 10:** after "q" almost always comes "u". At the start of a name, "a", "k" and "m" are popular. Write those odds down for every pair of letters, then roll dice letter by letter.
**Time:** ~1.5 h · **Builds on:** [5.1 Word counter + bag-of-words sentiment](../01-word-counter-and-bag-of-words-sentiment) · **Needs:** nothing extra (internet once for `names.txt`, ~230 KB)

## Why this matters
ChatGPT, Claude and every other LLM do one thing over and over: **predict the next token** given the ones before it, then pick one and repeat. This lesson builds that loop in its smallest form, with letters instead of tokens and one letter of memory instead of thousands. The ideas you meet here (probabilities for the next token, sampling, and a loss that measures surprise) are exactly the ones used to train and run LLMs.

## What you'll learn
- **Language model**: a probability for every possible next letter (or token), given what came before.
- **Counting is training**: for a bigram model, the best possible model is just the normalised counts.
- **Sampling**: picking the next letter at random *according to* its probability, which is why chatbots answer differently each time.
- **Negative log-likelihood (NLL) loss**: how surprised the model is by real data. Lower is better. GPT is trained on the same loss (cross-entropy).

## Before you start
```bash
pip install -r requirements.txt
```
- `numpy`: the 27×27 table of counts and the random sampling.

No API key needed. The first run downloads `names.txt` (32,033 names from Andrej Karpathy's *makemore* project, ~230 KB) into this folder. If you're offline, it falls back to 62 built-in names so the code still runs.

## Run it
1. From the course root:
   ```bash
   cd level-5-text-models/02-next-letter-predictor-bigram-name-generator
   pip install -r requirements.txt
   ```
2. Run it:
   ```bash
   python bigram.py
   ```

### What you should see
```
32033 names, e.g. ['emma', 'olivia', 'ava', 'isabella', 'sophia', 'charlotte']

After 'q' the most likely next letters are: [('u', '69%'), ('.', '10%'), ('i', '5%')]
Names most often start with: ['a', 'k', 'm', 'j', 's']

Invented names:
   reslaynn
   jaylon
   k
   siquxxtal
   brlyaha
   alanasmasseen
   c
   rinlema
   mbllilicakaisa
   eendoonn
   a
   na

loss (avg negative log-likelihood): 2.455  (random guessing would be 3.296)
```
What to look at:
- **"q" → "u" 69% of the time.** The model learned a real spelling rule just by counting.
- **The invented names.** Some sound real ("jaylon"), most are odd ("mbllilicakaisa"), and some are one letter long. The model only remembers ONE previous letter, so it has no idea how long the name already is or what it looked like 3 letters ago.
- **Loss 2.455 vs 3.296.** The model is much less surprised by real names than random guessing. That's your score to beat in 5.3.

## How it works
1. **`get_names.py` → `load_names()`** downloads `names.txt` once (to a temporary `.part` file first, so a broken download never leaves a half-file behind) and returns a list of names.
2. **The vocabulary.** `chars` is the 26 letters found in the names. `stoi` ("string to integer") gives each letter a number 1–26, and the special character `"."` gets 0. The dot marks both the **start** and the **end** of a name, so the model also learns how names begin and when to stop. `itos` is the reverse lookup. `V = 27`.
3. **Step 1, count.** `N` is a 27×27 table. For each name, e.g. `emma`, we look at `. e m m a .` and count every neighbouring pair (a **bigram**): `.e`, `em`, `mm`, `ma`, `a.`. `N[stoi["e"], stoi["m"]] += 1` means "m followed e once more".
   ```
            next letter →   .     a     b    ...
   current  .               0  4410  1306   ...   (how names START)
   letter   a            6640   556   541   ...
     ↓      ...
   ```
4. **Step 2, normalise.** Dividing each row by its total turns counts into probabilities: row `q` becomes P(next letter | current letter is q). Adding 1 to every count first (**smoothing**, like 5.1) means no pair is ever impossible. That's the whole "training"!
5. **The peek.** `P[stoi["q"]].argsort()[::-1][:3]` sorts row q from most to least likely and takes the top 3. (With the 62-name fallback list there is no "q", so the script uses the first letter of the first name instead.) `P[0]` is the row for `"."`: which letters names start with.
6. **Step 3, generate.** Start at `ix = 0` (the start dot). `rng.choice(V, p=P[ix])` rolls a weighted die: likely letters come up more often, but anything can happen. Append the letter, use it as the new "current letter", repeat until the dot (end) is drawn. `default_rng(42)` fixes the dice so you get the same names each run.
7. **Step 4, evaluate.** For every real bigram in every name, look up the probability the model gave it and take the log. The **average negative log-likelihood** is the loss:
   - if the model gave the real next letter probability 1.0 → −log(1) = 0 (no surprise);
   - probability 0.1 → 2.3; probability 0.01 → 4.6 (very surprised).
   Random guessing among 27 characters gives −log(1/27) = 3.296. Our 2.455 means the model has learned real structure.

## If something goes wrong
- **`(download failed: ...; using 62 built-in names)`** → you're offline or GitHub is blocked. The script still runs on the small list. To get the full list, download https://raw.githubusercontent.com/karpathy/makemore/master/names.txt in a browser and save it as `names.txt` in this folder.
- **`ModuleNotFoundError: No module named 'get_names'`** → run the script from inside this folder.
- **`ModuleNotFoundError: No module named 'numpy'`** → activate your virtual environment and run `pip install -r requirements.txt`.
- **You want different invented names** → change the seed in `np.random.default_rng(42)` (or remove the 42 for new names every run).

## Try this
1. **Two letters of memory.** Build a **trigram** model: predict the next letter from the previous *two*. Is the loss lower? Do the names look better?
   <details><summary>Solution</summary>

   Save as `trigram.py` in this folder:
   ```python
   import numpy as np
   from get_names import load_names

   names = load_names()
   chars = sorted(set("".join(names)))
   stoi = {c: i + 1 for i, c in enumerate(chars)}
   stoi["."] = 0
   itos = {i: c for c, i in stoi.items()}
   V = len(stoi)

   N = np.zeros((V, V, V), dtype=np.int32)          # N[a, b, c] = times c followed the pair (a, b)
   for name in names:
       seq = [".", "."] + list(name) + ["."]          # two start markers: the context is 2 letters
       for a, b, c in zip(seq, seq[1:], seq[2:]):
           N[stoi[a], stoi[b], stoi[c]] += 1
   P = (N + 1) / (N + 1).sum(axis=2, keepdims=True)

   rng = np.random.default_rng(42)
   for _ in range(8):
       out, a, b = [], 0, 0
       while True:
           c = rng.choice(V, p=P[a, b])
           if c == 0:
               break
           out.append(itos[c]); a, b = b, c
       print("  ", "".join(out))

   ll, n = 0.0, 0
   for name in names:
       seq = [".", "."] + list(name) + ["."]
       for a, b, c in zip(seq, seq[1:], seq[2:]):
           ll += np.log(P[stoi[a], stoi[b], stoi[c]]); n += 1
   print(f"trigram loss: {-ll / n:.3f}")
   ```
   The loss drops from 2.455 to 2.213 and names look more name-like ("briyael", "roslen", "mae"). But the table now has 27³ = 19,683 entries, and a 10-letter memory would need 27¹¹, more than there are stars you can see. Counting doesn't scale; neural networks (5.3) do.
   </details>
2. **Different lists.** Train on Pokémon, city names, band names or anything else, one per line.
   <details><summary>Hint</summary>

   Make a text file with one item per line, e.g. `cities.txt`, and change the first line of `bigram.py` to `names = load_names("cities.txt")`. Keep the items lowercase, or add `.lower()`. Spaces and punctuation work too: they just become extra characters in the vocabulary. With fewer than a few hundred items, results get repetitive.
   </details>
3. **Same model as a neural net.** Recreate the bigram table as a one-layer neural network in PyTorch (`pip install torch`) and check you reach the same loss. Karpathy does exactly this in the video below.
   <details><summary>Solution</summary>

   Save as `bigram_nn.py` in this folder:
   ```python
   import torch
   from get_names import load_names

   names = load_names()
   chars = sorted(set("".join(names)))
   stoi = {c: i + 1 for i, c in enumerate(chars)}
   stoi["."] = 0
   V = len(stoi)

   xs, ys = [], []                                  # every (current letter, next letter) pair
   for name in names:
       seq = ["."] + list(name) + ["."]
       for a, b in zip(seq, seq[1:]):
           xs.append(stoi[a]); ys.append(stoi[b])
   xs, ys = torch.tensor(xs), torch.tensor(ys)

   W = torch.randn(V, V, requires_grad=True)          # one weight per (current letter, next letter) pair
   opt = torch.optim.Adam([W], lr=0.1)
   for step in range(301):
       logits = W[xs]                                  # same as one_hot(xs) @ W, just faster
       loss = torch.nn.functional.cross_entropy(logits, ys)
       opt.zero_grad(); loss.backward(); opt.step()
       if step % 100 == 0:
           print(f"step {step:3d} | loss {loss.item():.3f}")
   ```
   The loss goes from ~3.7 to 2.454, matching the counting model's 2.455. Gradient descent rediscovers the count table: `softmax(W)` ends up almost equal to `P`. The difference: the neural version can grow (more context, hidden layers), which is the road to 5.3 and GPT.
   </details>

## Check yourself
1. Why does the model need the special `"."` character?
2. What does a loss of 3.296 mean here, and why is 2.455 better?
3. Why does the generator sometimes produce a one-letter name like "k"?
4. Why do chatbots give different answers to the same question, and how does this project show that?

<details><summary>Answers</summary>

1. It marks the start and end of every name, so the model learns which letters names begin with and when to stop. Without it, generation would never know how to start or end.
2. 3.296 is −log(1/27): the surprise of guessing uniformly among 27 characters. Lower loss means the model gives the real next letters higher probability, so it has learned real patterns.
3. After "k", the end dot has some probability (some names end in k), and the model doesn't remember that it only just started. One letter of memory can't know the name is too short.
4. They *sample* the next token from a probability distribution instead of always taking the most likely one. Here, `rng.choice(V, p=P[ix])` does the same thing; change the seed and you get different names.
</details>

## Learn more (optional)
- The spelled-out intro to language modeling: building makemore (Karpathy, watch this one, it's perfect for this project): https://www.youtube.com/watch?v=PaCmpygFfXo
- Karpathy's makemore repo (where `names.txt` comes from): https://github.com/karpathy/makemore

## Next
→ [5.3 · Tiny RNN name generator](../03-tiny-rnn-name-generator)
