"""Chat with your fine-tuned model in the terminal.

python chat.py                      # talks to sft.pt
python chat.py --model base.pt      # compare: the base model doesn't know the chat format
Type a message and press Enter. Empty line or Ctrl+C to quit. Each message is a fresh one-turn chat
(the model's context is only 96 characters).
"""
import argparse

from common import answer, load_model

p = argparse.ArgumentParser()
p.add_argument("--model", default="sft.pt")
p.add_argument("--temperature", type=float, default=0.7)
args = p.parse_args()

model = load_model(args.model)
print(f"Loaded {args.model}. Try: 'Uppercase: hello', 'Spell kitten', 'Say hello to Sam.', 'Who are you?'")
while True:
    try:
        user = input("\nyou> ").strip()
    except (EOFError, KeyboardInterrupt):
        break
    if not user:
        break
    print("bot>", answer(model, user, greedy=False, temperature=args.temperature))
