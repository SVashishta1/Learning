# Send one message to Claude and print the answer. This is the WHOLE thing, with no helper file, so you see every part.
import os
import sys

import anthropic

client = anthropic.Anthropic()                            # finds your key in the ANTHROPIC_API_KEY setting
model = os.getenv("CLAUDE_MODEL", "claude-opus-5-5")      # which AI model to use
question = " ".join(sys.argv[1:]) or "Explain what an API is to a 10-year-old, in 3 short sentences."

# Safety net: on these models, if a request is ever declined, Claude automatically retries on another model.
safety_net = {"betas": ["server-side-fallback-2026-07-01"], "fallbacks": "default"} if model in ("claude-opus-5-5", "claude-sonnet-5-5") else {}

response = client.beta.messages.create(
    model=model,
    max_tokens=1000,                                      # the longest reply allowed (a token is about 3/4 of a word)
    system="You are a friendly teacher.",                 # the AI's role and rules
    messages=[{"role": "user", "content": question}],     # the conversation so far: just our one message
    **safety_net,
)

# The response is made of "blocks"; we print the text ones.
print("".join(block.text for block in response.content if block.type == "text"))
print(f"\n(used {response.usage.input_tokens} tokens in, {response.usage.output_tokens} tokens out)")
