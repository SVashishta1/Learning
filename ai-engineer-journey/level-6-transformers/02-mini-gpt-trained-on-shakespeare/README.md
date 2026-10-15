# 6.2 · Mini-GPT trained on Shakespeare

**What you'll build:** a real GPT, with the same architecture as GPT-2 but ~2.7 million parameters instead of 1.5 billion. You train it from random numbers on the complete works of Shakespeare (1 MB of text), and it learns to write fake Shakespeare: character names, line breaks, old-fashioned words, even a play-like rhythm.
**Like you're 10:** you build a parrot's brain from LEGO, read it Shakespeare thousands of times, and it starts "speaking Shakespeare". It doesn't understand the plays, but it has learned what Shakespeare *sounds like*.
**Time:** ~4 h (including ~15–60 min of training on a laptop CPU) · **Builds on:** [6.1 Self-attention by hand](../01-self-attention-by-hand-numpy) · **Needs:** internet once (1 MB download); a GPU is optional (free on Google Colab)

## Why this matters
This is the same recipe behind ChatGPT, Claude and Llama, shrunk until it fits on a laptop: predict the next token, over and over, on lots of text. Building and training it yourself turns "LLM" from a magic word into code you understand line by line: embeddings, attention, residual connections, loss curves, sampling with temperature. Interviewers love candidates who can explain what happens *inside* the model they're calling through an API.

## What you'll learn
- **Next-token prediction**: the only training signal a GPT gets; everything it "knows" comes from guessing the next character.
- **Token + position embeddings**: what a character is plus where it sits (attention alone ignores order).
- **Transformer block**: attention (characters gather information from earlier characters) then a feed-forward layer (each position thinks on its own), with residual connections and LayerNorm.
- **Train vs. validation loss**: how you tell real learning from memorising.
- **Sampling**: temperature and top-k decide how adventurous the generated text is.

## Before you start
```bash
cd level-6-transformers/02-mini-gpt-trained-on-shakespeare
pip install -r requirements.txt
```
- `torch` (PyTorch): builds and trains the neural network, on CPU, NVIDIA GPU (`cuda`) or Apple Silicon (`mps`) automatically.

No API key. The first run downloads `tinyshakespeare` (1 MB) from GitHub into `input.txt`.

## Run it
1. From the course root: `cd level-6-transformers/02-mini-gpt-trained-on-shakespeare`
2. Quick wiring check (a tiny model, 30 steps, under a minute): `python train.py --smoke`
3. Real training (3,000 steps; ~15–60 min on a laptop CPU, ~3 min on a GPU): `python train.py`. It saves the model to `ckpt.pt`.
4. Generate 600 characters starting with "JULIET:": `python generate.py "JULIET:" 600`

### What you should see
`python train.py --smoke` (real output; times depend on your machine):
```
1,115,394 characters | vocab 65 | 0.11M parameters | cpu
iter     0 | train 4.345 | val 4.364 | 15s
iter    10 | train 3.711 | val 3.738 | 20s
iter    20 | train 3.405 | val 3.330 | 21s
iter    30 | train 3.231 | val 3.262 | 21s

ROMEO:
e aioauej
Mre,hopthnrdr rs o RssheutMs ar!o th  iu
```
Gibberish, as expected after 30 steps. Now the real run. This is real output from a 1,000-step run (a third of the default 3,000, on a busy CPU); your times will differ and the full run keeps improving:
```
1,115,394 characters | vocab 65 | 2.72M parameters | cpu
iter     0 | train 4.330 | val 4.334 | 72s
iter   250 | train 2.119 | val 2.180 | 593s
iter   500 | train 1.796 | val 1.905 | 923s
iter   750 | train 1.623 | val 1.782 | 1177s
iter  1000 | train 1.528 | val 1.709 | 1428s
```
and `python generate.py "JULIET:" 300` afterwards:
```
JULIET:
Ah, then where grace to be doth thy dail.

PRINCE EDWARD:
For that will us we heaven the warranter sprinds.

TYRREL:
Sir, I can to nother heaven. Will and this in out.
```
What to look at:
- **Loss starts at ~4.17–4.33**: that's about ln(65), the score of guessing uniformly among 65 characters. The model knows nothing yet.
- **Loss falls fast, then slowly.** After 1,000 steps (val 1.71) it already writes real character names (PRINCE EDWARD, TYRREL are real Shakespeare characters), speaker lines, punctuation and mostly real words, but the sentences make no sense. The full 3,000 steps bring val loss to roughly 1.5–1.6 and noticeably better words.
- **Train vs. val:** at step 1,000 train is 1.53 and val 1.71. A small gap is normal; if val stopped improving while train kept falling, the model would be memorising (overfitting).

## How it works
```
"ROMEO:\nWhat" ─► encode ─► [30, 27, 25, ...] ─► tok_emb + pos_emb ─► Block × 6 ─► ln_f ─► head ─► 65 scores per position
                                                  (attention + feed-forward)                       │
                                    training: cross_entropy vs. the real next character ◄──────────┤
                                    generating: softmax → sample → append → repeat ◄────────────────┘
```

### `model.py` (read top to bottom)
1. **`Config`** holds the sizes: `vocab_size` 65 characters, `block_size` 128 (how many previous characters it can see), `n_embd` 192 (numbers per character), 6 heads, 6 layers, 10% dropout.
2. **`CausalSelfAttention`** is 6.1 made trainable and batched. One `nn.Linear` (`self.qkv`) computes Q, K and V for all heads at once; `.view(...).transpose(1, 2)` splits them into 6 heads of 32 numbers. Scores are scaled by √32, future positions are blocked with `masked_fill(~self.mask...)`, softmax turns them into weights, and `self.proj` (Wo) mixes the heads back together.
3. **`FeedForward`** is a small two-layer network (192 → 768 → 192 with GELU) applied to each position separately: after the characters "talk" (attention), each one "thinks".
4. **`Block`** does `x = x + attn(ln1(x))` then `x = x + ffwd(ln2(x))`. The `x + ...` is a **residual connection**: an information highway that lets deep networks train. **LayerNorm** keeps the numbers in a healthy range.
5. **`GPT.forward`** adds `tok_emb` (what each character is) and `pos_emb` (where it is), runs the 6 blocks, normalises, and `head` turns each position's 192 numbers into 65 scores (logits) for the next character. With `targets`, it also returns the **cross-entropy loss**: how surprised the model was by the real next character.
6. **`GPT.generate`** loops: take the last 128 characters, get the scores for the next one, divide by `temperature`, keep only the `top_k` best, sample one with `torch.multinomial`, append it, repeat.

### `train.py`
1. **Data.** Downloads `input.txt` if missing, builds the vocabulary (`chars`, every distinct character) and `encode`/`decode` between text and ids, then splits 90% for training and the last 10% for validation (text the model never trains on).
2. **`get_batch(split)`** picks 32 random windows of 128 characters. The targets `y` are the same windows shifted by one character: at every position the answer is "the next character". One batch = 32 × 128 = 4,096 predictions.
3. **`estimate_loss()`** averages the loss over 20 batches of each split with dropout off (`model.eval()`), for a steady, honest number.
4. **The loop** (3,000 steps, or 30 with `--smoke`): get a batch, compute the loss, `zero_grad` → `backward` (backprop from Level 2) → `clip_grad_norm_` (stops rare huge updates) → `AdamW.step()`. Every 300 steps it prints train/val loss and the elapsed time.
5. **Save and sample.** `torch.save` writes the weights, the config and the vocabulary to `ckpt.pt`, then it generates a short sample starting with "ROMEO:".

### `generate.py`
Loads `ckpt.pt`, rebuilds the model from the saved config, encodes your prompt (characters Shakespeare never used are skipped), and prints `n` new characters sampled with `temperature=0.8, top_k=20`.

**Scale:** ChatGPT is this, plus a BPE tokenizer (5.6), roughly 100,000 times more parameters and data, and extra training to follow instructions and be helpful (instruction tuning and RLHF).

## If something goes wrong
- **`urllib.error.URLError` on the first run** → no internet, or GitHub is blocked. Download https://raw.githubusercontent.com/karpathy/char-rnn/master/data/tinyshakespeare/input.txt in a browser and save it as `input.txt` in this folder.
- **Training is very slow** → normal on CPU (each step processes 4,096 predictions through 6 layers). Try `--smoke` first, close other apps, or run on Google Colab with a GPU (Runtime → Change runtime type → GPU; it picks `cuda` automatically).
- **`No ckpt.pt found`** from `generate.py` → train first; `generate.py` needs the saved model. Note that `--smoke` also writes a (tiny, bad) `ckpt.pt`.
- **`RuntimeError: CUDA out of memory`** → lower `batch_size` (32 → 16) in the `max_iters, batch_size, eval_every = ...` line.
- **Output is still gibberish after the full run** → check the final val loss. Above ~2.0 means training was cut short or something changed; run the full 3,000 steps.

## Try this
1. **Play with temperature.** In `generate.py`, change `temperature=0.8` to `0.3`, then to `1.5`, and generate again. What changes?
   <details><summary>Hint</summary>

   Low temperature makes the most likely characters even more likely: safe, repetitive text ("the the the" or the same phrase looping). High temperature flattens the choices: more creative but more misspelled. This is the same `temperature` setting chat APIs offer.
   </details>
2. **A bigger brain.** Train with `n_layer=8, n_embd=256, n_head=8`. Is it slower? Does the val loss get lower?
   <details><summary>Solution</summary>

   Change the config line in `train.py` to:
   ```python
   cfg = Config(vocab_size=len(chars), **({"n_layer": 2, "n_embd": 64, "n_head": 4, "block_size": 32} if SMOKE
                                          else {"n_layer": 8, "n_embd": 256, "n_head": 8}))
   ```
   `n_embd` must be divisible by `n_head` (each head gets `n_embd / n_head` numbers). You'll see about 6.4M parameters, slower steps and usually a lower val loss for the same number of steps, until the model starts overfitting this small dataset. That trade-off (bigger model vs. more data vs. more compute) is what "scaling laws" are about.
   </details>
3. **Your own text.** Train on something else: a book from Project Gutenberg, your chat exports, or Python code.
   <details><summary>Hint</summary>

   Rename the old `input.txt` and put your text in a new `input.txt` (UTF-8, ideally 500 KB or more; tiny files get memorised). Delete `ckpt.pt`, run `python train.py`, then `python generate.py "def " 400` for code or a typical opening for your text. Going further: replace the character `encode`/`decode` with your BPE tokenizer from 5.6 so each token is a word piece; then `vocab_size` becomes your BPE vocabulary size.
   </details>

## Check yourself
1. Why does the loss start at about 4.17, and what does a loss of 1.5 mean in comparison?
2. Why are the targets the inputs shifted by one character?
3. What would go wrong without `pos_emb`?
4. Validation loss stops improving while training loss keeps dropping. What is happening and what can you do?

<details><summary>Answers</summary>

1. ln(65) ≈ 4.17 is the loss of guessing all 65 characters equally. Loss 1.5 means the model gives the right next character a probability of about e^-1.5 ≈ 22% on average, far better than 1/65 ≈ 1.5%.
2. So every position learns to predict the character that actually comes next. One window of 128 characters gives 128 training examples at once.
3. Attention would see a bag of characters with no order, so "dog bites man" and "man bites dog" would look the same, and the model couldn't learn spelling or line structure.
4. Overfitting: it's memorising the training text instead of learning general patterns. Stop earlier, add dropout, use a smaller model, or get more data.
</details>

## Learn more (optional)
- Let's build GPT: from scratch, in code, spelled out (Karpathy, follow along line by line): https://www.youtube.com/watch?v=kCc8FmEb1nY
- nanoGPT (the grown-up version of this code): https://github.com/karpathy/nanoGPT
- The Illustrated GPT-2 (Jay Alammar): https://jalammar.github.io/illustrated-gpt2/

## Next
→ [6.3 · Fine-tune a small LLM with LoRA](../03-fine-tune-a-small-llm-with-lora)
