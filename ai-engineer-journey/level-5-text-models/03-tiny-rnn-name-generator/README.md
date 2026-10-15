# 5.3 · Tiny RNN name generator

**What you'll build:** a small **recurrent neural network** (a GRU) that reads names letter by letter, keeps a *memory* of everything so far, and invents new names that sound much more real than the bigram model's.
**Like you're 10:** the bigram model only remembered the *last* letter, like a goldfish. The RNN keeps a little notebook it updates after every letter ("we started with 'k', we've had a vowel, it's getting long, time to end"). Better memory, better names.
**Time:** ~2 h · **Builds on:** [5.2 Bigram name generator](../02-next-letter-predictor-bigram-name-generator) and [4.1 MNIST](../../level-4-computer-vision/01-mnist-digits-simple-neural-net) (the PyTorch training loop) · **Needs:** nothing extra (CPU is fine)

## Why this matters
Language depends on order and context: "not bad" means the opposite of "bad, not". Recurrent networks were the first neural networks that read text in order and *remember*, and they powered Google Translate, phone keyboards and speech recognition for years. Transformers (Level 6) replaced them, but they solve the same problem, and the ideas here (embeddings, predicting the next token at every position, padding, temperature) carry straight over to GPT.

## What you'll learn
- **Embedding**: each letter becomes a small learned vector of numbers (a preview of 5.4).
- **Hidden state**: the RNN's memory, a vector updated after every letter.
- **Training on every position at once**: input `.emma`, target `emma.`, so one name gives 5 practice predictions.
- **Padding + `ignore_index`**: how to batch names of different lengths without the padding confusing the loss.
- **Temperature**: one number that makes generation safer or wilder (ChatGPT has the same knob).

## Before you start
```bash
pip install -r requirements.txt
```
- `torch`: the GRU network, loss and optimizer.

No API key needed. `names.txt` (32,033 names, the same list as 5.2) is already in this folder. If you delete it, `get_names.py` downloads it again, or falls back to 62 built-in names when offline.

## Run it
1. From the course root:
   ```bash
   cd level-5-text-models/03-tiny-rnn-name-generator
   pip install -r requirements.txt
   ```
2. Quick wiring check (500 names, 50 steps, a few seconds):
   ```bash
   python rnn_names.py --smoke
   ```
3. Train for real (3,000 steps, about 1–3 minutes on a laptop CPU):
   ```bash
   python rnn_names.py
   ```

### What you should see
```
step   500 | loss 2.089 | sample: amaria
step  1000 | loss 2.053 | sample: zani
step  1500 | loss 1.967 | sample: tammi
step  2000 | loss 2.033 | sample: eret
step  2500 | loss 1.982 | sample: mahtobat
step  3000 | loss 1.880 | sample: pellip

loss on all 32033 names: 1.894  (the bigram model in 5.2 got 2.455)

Fresh names (temperature 0.8): daizy, lovania, kithi, amarie, kaidan, jaylyn, taymin, zamaryah, salamani, liliana
Wild names   (temperature 1.5): alizandare, famet, ojgatira, enai, hazufurreyh
112/200 samples are brand-new names not in the dataset, e.g. ['zacaria', 'jersen', 'yusefia', 'nylian', 'erenzo', 'emerley']
```
What to look at:
- **Loss 1.894 vs the bigram's 2.455.** Both are measured the same way (average surprise per letter over all names), so this is a fair comparison: memory helps a lot.
- **The names.** "daizy", "kaidan", "liliana" sound real, and lengths are sensible. Compare with 5.2's "mbllilicakaisa".
- **Temperature 1.5** gives stranger names ("hazufurreyh"): more creative, less correct.
- **112/200 are new.** The other 88 are real names the model reproduced, because real names are its most likely outputs at temperature 0.8.

## How it works
```
input:   .    e    m    m    a
         │    │    │    │    │      embed: letter → 24 numbers
         ▼    ▼    ▼    ▼    ▼
 h0 ──► GRU ─►GRU ─►GRU ─►GRU ─►GRU      h = memory (128 numbers), passed along
         │    │    │    │    │      head: memory → 27 scores
         ▼    ▼    ▼    ▼    ▼
target:  e    m    m    a    .      loss at every position
```
1. **Vocabulary.** `chars` is `"."` plus the 26 letters; `stoi` maps each to 0–26. `"."` (index 0) marks start and end, exactly as in 5.2.
2. **`NameRNN`** has three parts:
   - `nn.Embedding(vocab, 24)`: a lookup table that turns each letter number into a learned vector of 24 numbers. Similar letters (e.g. vowels) end up with similar vectors.
   - `nn.GRU(24, 128, batch_first=True)`: the recurrent part. At each letter it combines the letter's vector with its current memory `h` (128 numbers) to produce a new memory. A **GRU** (gated recurrent unit) has learnable "gates" that decide what to keep and what to forget, which helps it remember over longer distances than a plain RNN.
   - `nn.Linear(128, vocab)`: turns the memory at each position into 27 scores for the next letter.
   `forward(x, h)` returns the scores for every position and the final memory, so generation can continue from it.
3. **`make_batch(batch_names)`** turns names into tensors. `'emma'` becomes input `.emma` and target `emma.`: at every position, the target is the next letter. This is called **teacher forcing**: during training, the model always sees the *real* previous letters, not its own guesses. Names have different lengths, so shorter ones are padded: input padding is 0, target padding is **-100**. `CrossEntropyLoss(ignore_index=-100)` skips those positions, so padding never counts as a mistake.
4. **The training loop** (3,000 steps): pick 64 random names, build a batch, predict, compute the loss (`reshape(-1, V)` flattens all positions of all names into one long list), backprop, and update with **Adam**. `clip_grad_norm_(..., 1.0)` caps the size of the gradients. RNNs multiply through many time steps, and gradients can occasionally explode to huge values; clipping stops one bad batch from wrecking the model. Every 500 steps it prints the batch loss and one sample name, so you can watch it improve.
5. **`full_loss(model)`** computes the average loss over *all* 32,033 names (in chunks of 1,000), counting only real letters. That's the same measurement as 5.2's loss, so the two numbers are directly comparable. The per-step losses above it are from single random batches, so they jump around.
6. **`sample(model, temperature)`** generates a name: start with `"."`, get scores, divide them by the **temperature**, softmax them into probabilities, draw a letter with `torch.multinomial`, feed it back in together with the memory `h`, and stop at `"."` or after 20 letters.
   - temperature < 1 sharpens the probabilities (safer, more common choices);
   - temperature > 1 flattens them (rare letters get a real chance: creative, then weird).
7. **The last line** generates 200 names and counts how many aren't in the training list.

## If something goes wrong
- **Training is very slow (more than 10 minutes)** → other programs are using the CPU, or PyTorch is fighting itself for cores. Try `OMP_NUM_THREADS=2 python rnn_names.py` (Linux/macOS) or close heavy apps.
- **`ModuleNotFoundError: No module named 'torch'`** → activate your virtual environment and run `pip install -r requirements.txt`.
- **`KeyError` in `sample(..., start=...)`** (after Try this 2) → the start text must use only lowercase letters that appear in the names.
- **`(download failed ...)`** → you deleted `names.txt` and are offline. Restore it from the repo, or see 5.2's download tip.
- **Your numbers differ slightly from the sample** → different PyTorch versions or hardware give slightly different random numbers. Losses around 1.9 are normal.

## Try this
1. **Other memory cells.** Replace `nn.GRU` with `nn.LSTM`, then with plain `nn.RNN`. Which reaches the lowest loss?
   <details><summary>Hint</summary>

   Just change `nn.GRU(` to `nn.LSTM(` or `nn.RNN(`; nothing else needs to change (the LSTM's memory is a pair `(h, c)`, but the code passes it around without looking inside). When checked: LSTM 1.885, GRU 1.894, plain RNN 2.004 on all names. Gated cells (GRU, LSTM) remember better than a plain RNN.
   </details>
2. **Names that start with K.** Let `sample()` take a starting text, so `sample(model, start="k")` only invents names beginning with "k".
   <details><summary>Solution</summary>

   Replace the first lines of `sample`:
   ```python
   @torch.no_grad()
   def sample(model, temperature=0.8, max_len=20, start=""):
       out = list(start)
       x = torch.tensor([[0] + [stoi[c] for c in start]])   # feed ".k" so the memory knows the name starts with k
       h = None
   ```
   (the loop stays the same: it reads the scores after the *last* input letter). Then add at the end:
   ```python
   print("K names:", ", ".join(sample(model, start="k") for _ in range(8)))
   ```
   This is exactly how a chatbot continues your prompt: the prompt fills the memory, then generation carries on from there.
   </details>
3. **Different text.** Train on song lyrics or a short story instead of names, a preview of the mini-GPT in 6.2.
   <details><summary>Hint</summary>

   Make a text file, split it into lines (each line becomes one "name"), e.g. `names = [l.strip().lower() for l in open("lyrics.txt", encoding="utf-8") if l.strip()]`, and set `max_len` in `sample` to ~80. Spaces and punctuation become extra characters automatically. Increase `hidden` to 256 and `steps` to 5,000+ for better results. You'll see why transformers took over: long lines are hard for a small RNN to remember.
   </details>

## Check yourself
1. What does the hidden state `h` contain, and why does the bigram model not have one?
2. Why is the target `emma.` when the input is `.emma`?
3. Why are padded target positions set to -100?
4. You want safer, more common names. Should you raise or lower the temperature? Why?

<details><summary>Answers</summary>

1. A vector of 128 numbers summarising everything the network has read so far in this name. The bigram model only looks at the current letter, so it has no memory of earlier letters.
2. At each position the model must predict the *next* letter. Shifting by one lines up every input letter with the letter that follows it, so one name gives a training example at every position.
3. `CrossEntropyLoss(ignore_index=-100)` skips positions with that value, so padding (which isn't real data) doesn't count as a right or wrong prediction.
4. Lower it (e.g. 0.5). Dividing scores by a small number makes the differences bigger, so the most likely letters win even more often.
</details>

## Learn more (optional)
- Recurrent Neural Networks, Clearly Explained (StatQuest): https://www.youtube.com/results?search_query=statquest+recurrent+neural+networks+clearly+explained
- LSTM, Clearly Explained (StatQuest): https://www.youtube.com/results?search_query=statquest+long+short-term+memory+lstm+clearly+explained
- Karpathy, "The Unreasonable Effectiveness of RNNs" (classic blog post): http://karpathy.github.io/2015/05/21/rnn-effectiveness/

## Next
→ [5.4 · Embeddings: find similar words and sentences](../04-embeddings-find-similar-sentences)
