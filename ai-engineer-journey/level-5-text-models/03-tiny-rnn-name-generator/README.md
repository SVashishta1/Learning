# 5.3 · Tiny RNN name generator

**What you build:** a small **recurrent neural network** (a GRU) that reads names letter by letter, keeps a *memory* of everything so far, and invents new names that sound much more real than the bigram model's.
**Like you're 10:** the bigram model only remembered the *last* letter, like a goldfish. The RNN keeps a little notebook it updates after every letter ("we started with 'k', we've had a vowel, it's getting long, time to end"). Better memory, better names.

## Run it
```bash
cd level-5-text-models/03-tiny-rnn-name-generator
pip install -r requirements.txt
python rnn_names.py --smoke     # 10-second check
python rnn_names.py             # ~3 minutes on CPU
```
Watch the samples improve during training. The loss should drop below the bigram's 2.45 (to around 2.0–2.1).

## Key ideas
- **Embedding:** each letter becomes a learned vector (a preview of 5.4).
- **Hidden state `h`:** the RNN's memory, passed from step to step.
- **Teacher forcing:** during training the input is the real name shifted by one, so the model predicts the next letter at *every* position at once.
- **Padding + `ignore_index`:** names have different lengths; padded positions are ignored by the loss.
- **Temperature:** divide the scores before softmax. Low = safe and common, high = creative and weird. ChatGPT has this same knob.
- **Gradient clipping:** stops RNN training from exploding.

## Your turn
1. Replace `nn.GRU` with `nn.LSTM`, or with plain `nn.RNN`. Which learns fastest?
2. Condition on a first letter: start sampling from ".k" to get names beginning with K.
3. Train on song lyrics or Shakespeare instead of names (a preview of the mini-GPT in 6.2).

## Watch
- Recurrent Neural Networks, Clearly Explained (StatQuest): https://www.youtube.com/results?search_query=statquest+recurrent+neural+networks+clearly+explained
- LSTM, Clearly Explained (StatQuest): https://www.youtube.com/results?search_query=statquest+long+short-term+memory+lstm+clearly+explained
- Karpathy, "The Unreasonable Effectiveness of RNNs" (classic blog post): http://karpathy.github.io/2015/05/21/rnn-effectiveness/
