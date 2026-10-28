"""Capstone stage 5a: chat with your model in the terminal (multi-turn).

python chat_cli.py                       # interactive; empty line or Ctrl+C quits, /reset starts over
python chat_cli.py -p "Who are you?"     # one question, one answer, then exit
"""
import argparse

from common import load_model, load_tokenizer, reply

p = argparse.ArgumentParser()
p.add_argument("-p", "--prompt", help="ask one question and exit")
p.add_argument("--model", default="chat.pt")
p.add_argument("--temperature", type=float, default=0.5)
args = p.parse_args()

tok = load_tokenizer()
model = load_model(args.model)
if args.prompt:
    print(reply(model, tok, [], args.prompt, temperature=args.temperature)[0])
    raise SystemExit
print("TinyChat is ready. Try: Hello! / Who are you? / What is the capital of Japan? / My name is Sam.")
history = []
while True:
    try:
        user = input("\nyou> ").strip()
    except (EOFError, KeyboardInterrupt):
        break
    if not user:
        break
    if user == "/reset":
        history = []
        print("(conversation cleared)")
        continue
    answer, history = reply(model, tok, history, user, temperature=args.temperature)
    print("bot>", answer)
