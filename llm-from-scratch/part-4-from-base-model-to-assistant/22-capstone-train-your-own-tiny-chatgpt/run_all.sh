#!/usr/bin/env bash
# Capstone "speedrun" (in the spirit of nanochat's speedrun.sh): every stage, in order.
#   bash run_all.sh            # CPU defaults, ~20-40 minutes in total
# Afterwards: python chat_cli.py   or   python chat_web.py
set -euo pipefail                  # stop at the first error; unset variables are errors

echo "== 1/4 data: download, clean, deduplicate"
python data.py
echo "== 2/4 tokenizer: train BPE, tokenize the corpus"
python tokenizer.py
echo "== 3/4 pretraining: base model"
python pretrain.py
echo "== 4/4 SFT: chat model"
python sft.py
echo "== done. Chat with it:  python chat_cli.py   or   python chat_web.py"
