# A terminal chatbot that REMEMBERS the conversation and types its replies live.
# Usage: python chatbot.py            or give it a personality:  python chatbot.py "You are a grumpy cat."
import sys

import ai

personality = " ".join(sys.argv[1:]) or "You are a kind study buddy. Keep answers short and ask a follow-up question."
conversation = []          # THE MEMORY: every message so far, in order

print("Chatbot ready! Type 'bye' to quit.\n")
while True:
    you = input("you: ").strip()
    if you.lower() in {"bye", "quit", "exit"}:
        break
    conversation.append({"role": "user", "content": you})

    print("bot: ", end="", flush=True)
    reply = ""
    for piece in ai.stream(conversation, system=personality):    # the reply arrives word by word
        print(piece, end="", flush=True)
        reply += piece
    print("\n")

    conversation.append({"role": "assistant", "content": reply})  # remember what the bot said too

print(f"Bye! We exchanged {len(conversation)} messages.")
