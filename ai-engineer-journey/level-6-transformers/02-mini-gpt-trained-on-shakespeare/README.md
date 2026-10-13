# 6.2 · Mini-GPT trained on Shakespeare

**What you build:** a real GPT, with the same architecture as GPT-2 but ~2.7M parameters instead of 1.5 billion. You train it from random weights on the complete works of Shakespeare (1 MB of text), and it learns to write fake Shakespeare: names, line breaks, archaic words, even iambic-ish rhythm.
**Like you're 10:** you build a parrot's brain from LEGO, read it Shakespeare thousands of times, and it starts "speaking Shakespeare". It doesn't understand the plays, but it has learned what Shakespeare *sounds like*.

## Run it
```bash
cd level-6-transformers/02-mini-gpt-trained-on-shakespeare
pip install -r requirements.txt
python train.py --smoke        # few-second check
python train.py                # downloads tinyshakespeare (1 MB) and trains
python generate.py "JULIET:" 600
```
Validation loss should fall from ~4.2 (random) to ~1.5. Under ~1.6 the text starts looking like plays. Free GPU: run it on Google Colab.

## Map of the code (`model.py`)
| Class | Job |
|-------|-----|
| `tok_emb` + `pos_emb` | what each character is + where it sits (attention ignores order, so position must be added) |
| `CausalSelfAttention` | 6.1 batched: characters gather information from earlier characters |
| `FeedForward` | each position processes what it gathered |
| `Block` | attention + feed-forward with **residual connections** and **LayerNorm** |
| `GPT.generate` | predict → sample → append → repeat (with temperature and top-k) |

## Key ideas
- **Next-token prediction** is the *entire* training signal of GPT-style models.
- **Train vs. val loss:** if val stops improving while train keeps falling, you're overfitting. Add dropout or stop earlier.
- **Scale:** ChatGPT is this, plus a BPE tokenizer (5.6), plus ~10,000× more parameters and data, plus instruction tuning and RLHF.

## Your turn
1. Train on your own text: your chats, a favourite book from Project Gutenberg, or Python code.
2. Double `n_layer` and `n_embd`. Is it slower? Better? Watch the val loss.
3. Swap the character tokenizer for your BPE tokenizer from 5.6.

## Watch (follow along, line by line)
- Let's build GPT: from scratch, in code, spelled out (Karpathy): https://www.youtube.com/watch?v=kCc8FmEb1nY
- nanoGPT (the grown-up version): https://github.com/karpathy/nanoGPT
