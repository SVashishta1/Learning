# 6.5 · Run an open LLM on your laptop

**What you'll build:** two ways to run a real chat model **on your own machine**, free and private, with no API key:
- **Part A, Ollama:** the easiest way to run Llama, Qwen or Gemma locally, plus a Python chat client with streaming and memory.
- **Part B, transformers:** load a small model yourself and print the **chat template**, the exact text the model sees behind a "chat".

**Like you're 10:** using an API is ordering pizza: fast, great, but you pay each time and the restaurant sees your order. Running locally is cooking at home: you need a kitchen (RAM/GPU), the food may be simpler, but it's free and private.
**Time:** ~1 h · **Builds on:** [6.4 Translator & summariser](../04-translator-and-summarizer-with-huggingface) · **Needs:** Part A: [Ollama](https://ollama.com/download) and ~8 GB RAM. Part B: internet for the first run (~720 MB download). No API key.

## Why this matters
Not every AI feature can send data to a cloud API: hospitals, banks and lawyers often must keep text on their own machines, and some apps need to work offline or at zero cost per request. Open models such as Llama, Qwen and Gemma, run with tools like Ollama, are how teams do this. Seeing the raw chat template also removes the mystery from every chat product, including the Claude API you'll use in Level 7.

## What you'll learn
- **Local inference**: running a model on your own hardware instead of calling someone else's server.
- **Quantization**: storing weights in 4 bits instead of 16 or 32 so a 3B-parameter model fits in ~2 GB.
- **Chat template**: a chat is just one long text with special tokens marking who speaks; the model simply continues it.
- **Streaming**: sending tokens as soon as they're generated so replies appear word by word.
- **Memory is just history**: the model remembers nothing; your code resends the whole conversation every turn.

## Before you start
```bash
cd level-6-transformers/05-run-an-open-llm-on-your-laptop
pip install -r requirements.txt
```
- `httpx`: makes HTTP requests to Ollama's local API (Part A).
- `torch`, `transformers`: load and run the model yourself (Part B).

For Part A, also:
1. Install Ollama from https://ollama.com/download (Windows, macOS, Linux). It runs in the background as a small server on port 11434.
2. Download a model in a terminal: `ollama pull llama3.2:3b` (~2 GB; needs ~8 GB RAM). On 4 GB RAM use `ollama pull llama3.2:1b`.
3. Check it works: `ollama run llama3.2:3b "Say hi"`.

No API key needed for either part.

## Run it
1. From the course root: `cd level-6-transformers/05-run-an-open-llm-on-your-laptop`
2. Part A: `python ollama_chat.py` (or another model you've pulled: `python ollama_chat.py qwen2.5:3b`). Type a question, press Enter; type `quit` to leave.
3. Part B: `python transformers_chat.py` (downloads SmolLM2-360M-Instruct, ~720 MB, the first time).

### What you should see
Part A (your model's words will differ, since it samples):
```
Chatting with llama3.2:3b running on YOUR machine. Type 'quit' to exit.

you> What is a neural network?
bot> A neural network is a computer program inspired by the brain. It's made of layers of simple units that pass numbers to each other. By looking at lots of examples and adjusting its connections, it learns patterns, like recognising cats in photos or predicting the next word.

you> Give me a one-line example.
bot> Your phone's face unlock uses a neural network that learned what your face looks like.

you> quit
```
The reply appears word by word (streaming). Notice that "Give me a one-line example" works because the script resent the first question and answer too.

Part B (the template part is exact; the answer and speed are representative and vary by machine):
```
=== What the model ACTUALLY sees (chat template) ===
<|im_start|>system
You are a concise assistant.<|im_end|>
<|im_start|>user
Explain what a neural network is in two sentences.<|im_end|>
<|im_start|>assistant

=== Answer ===
A neural network is a computer model made of layers of connected nodes that learn patterns from data. It improves by adjusting the strength of its connections whenever its predictions are wrong.

38 tokens in 2.9s = 13.1 tokens/sec on your machine
```
Look at the template: `<|im_start|>` and `<|im_end|>` mark each message, and the text ends with `assistant` and a new line, an open invitation for the model to keep writing.

## How it works
```
ollama_chat.py ──POST /api/chat {model, messages: [whole history], stream: true}──► Ollama (localhost:11434)
       ▲                                                                              │ runs llama3.2 on your CPU/GPU
       └──────────── one JSON line per token: {"message": {"content": "Hi"}} ◄────────┘
```

### Part A: `ollama_chat.py`
1. **`MODEL`** comes from the command line (`sys.argv[1]`) or defaults to `llama3.2:3b`. **`history`** starts with a system message that sets the bot's personality.
2. **The loop** reads your input with `input()`. `quit`, `exit`, Ctrl+D or Ctrl+C end the chat; empty lines are skipped. Your message is appended to `history` as `{"role": "user", ...}`.
3. **`httpx.stream("POST", URL, ...)`** sends the *whole* `history` to Ollama with `"stream": True`. If Ollama answers with an error (`status_code != 200`, e.g. the model isn't pulled), the script prints Ollama's message and exits.
4. **`r.iter_lines()`** reads the reply as it arrives: each line is a small JSON object with the next piece of text. The script prints each piece immediately (`flush=True`) and collects it in `reply`.
5. **`httpx.ConnectError`** means nothing is listening on port 11434, so the script tells you to start Ollama.
6. **Memory**: the full `reply` is appended to `history` as `{"role": "assistant", ...}`. Next turn, the model sees everything again. That's all "chat memory" is, and why long chats get slower and (with APIs) more expensive.

### Part B: `transformers_chat.py`
1. **Load** the tokenizer and model for `SmolLM2-360M-Instruct`, a small instruction-tuned model.
2. **`tok.apply_chat_template(messages, tokenize=False, add_generation_prompt=True)`** turns the list of messages into the single string the model was trained on, and prints it. `add_generation_prompt=True` adds the final `<|im_start|>assistant` line so the model knows it's its turn.
3. **`model.generate(..., do_sample=True, temperature=0.7, top_p=0.9)`** writes up to 80 tokens. `temperature` below 1 makes choices a bit safer; `top_p=0.9` only samples from the most likely tokens that together make up 90% of the probability (a cousin of 6.2's top-k).
4. **Decode only the new part**: `out[0][ids["input_ids"].shape[1]:]` slices off the prompt tokens so you print just the answer, then the script reports tokens per second.

**Local vs. API trade-offs:**

| | Local open model | Hosted API (Claude etc.) |
|--|--|--|
| Cost | free after hardware | pay per token |
| Privacy | data never leaves your machine | sent to the provider |
| Quality | good for small tasks | state of the art |
| Speed | depends on your machine | fast, scalable |
| Ops work | you manage it | none |

## If something goes wrong
- **`Ollama isn't running...`** → open the Ollama app (or run `ollama serve` in another terminal), then try again.
- **`Ollama error 404: {"error":"model 'llama3.2:3b' not found"}`** → you haven't downloaded that model. Run `ollama pull llama3.2:3b`, or pass the name of a model you have (`ollama list` shows them).
- **Replies are very slow or the computer freezes** → the model is too big for your RAM. Try `llama3.2:1b` or `qwen2.5:0.5b`, and close other apps.
- **`httpx.ReadTimeout`** → the first reply after starting Ollama includes loading the model into memory, which can take a while on slow disks. Run the script again; the `timeout=120` is generous after that.
- **Part B: `OSError: We couldn't connect to 'https://huggingface.co'`** → the first run needs internet to download the model; after that it's cached.

## Try this
1. **Model shoot-out.** Pull two more models (e.g. `qwen2.5:3b`, `gemma3:4b`) and ask each the same 3 questions. Which is fastest? Which answers best?
   <details><summary>Hint</summary>

   Ollama's last streamed line has `"done": true` plus `eval_count` (tokens generated) and `eval_duration` (nanoseconds). Inside the `for line in r.iter_lines():` loop, add:
   ```python
   data = json.loads(line)
   if data.get("done"):
       print(f"\n[{data['eval_count'] / data['eval_duration'] * 1e9:.1f} tokens/sec]")
   ```
   </details>
2. **Local embeddings.** Ollama can also make embeddings: `ollama pull nomic-embed-text`. Use them to find which of three sentences is closest to a question, redoing 5.4's semantic search fully locally.
   <details><summary>Solution</summary>

   ```python
   import httpx

   sentences = ["The cat sat on the mat.", "Stocks fell sharply today.", "A kitten is sleeping on the rug."]
   question = "Where is the pet resting?"
   r = httpx.post("http://localhost:11434/api/embed",
                  json={"model": "nomic-embed-text", "input": sentences + [question]}, timeout=120)
   *vecs, q = r.json()["embeddings"]

   def cosine(a, b):
       dot = sum(x * y for x, y in zip(a, b))
       return dot / (sum(x * x for x in a) ** 0.5 * sum(y * y for y in b) ** 0.5)

   for s, v in sorted(zip(sentences, vecs), key=lambda p: -cosine(q, p[1])):
       print(f"{cosine(q, v):.3f}  {s}")
   ```
   The two pet sentences should score highest even though they share almost no words with the question.
   </details>
3. **Chat with your pirate.** Load the `pirate-lora` adapter you trained in 6.3 on top of `SmolLM2-135M-Instruct` in `transformers_chat.py` and turn the script into a loop that keeps `messages` as history.
   <details><summary>Hint</summary>

   Change `MODEL_ID` to `"HuggingFaceTB/SmolLM2-135M-Instruct"`, then after loading: `from peft import PeftModel` and `model = PeftModel.from_pretrained(model, "../03-fine-tune-a-small-llm-with-lora/pirate-lora")` (run `pip install peft`). Wrap the template/generate/decode lines in `while True:`, read `input()`, append `{"role": "user", ...}` before generating and `{"role": "assistant", "content": answer}` after, exactly like `history` in Part A.
   </details>

## Check yourself
1. The model has no memory. So how does the bot in Part A understand "Give me a one-line example"?
2. What does `add_generation_prompt=True` add, and why does the model need it?
3. Why can a 3-billion-parameter model fit in about 2 GB with Ollama?
4. Name one situation where you'd choose a local model over the Claude API, and one where you wouldn't.

<details><summary>Answers</summary>

1. The script resends the whole `history` (system message, earlier questions and earlier answers) with every request, so the model reads the earlier conversation each time.
2. It adds the opening of an assistant message (`<|im_start|>assistant` + new line). Without it the model might continue *your* message instead of starting its own reply.
3. Quantization: each weight is stored in ~4 bits instead of 16 or 32. 3 billion × 4 bits ≈ 1.5 GB, plus a little overhead.
4. Local: private patient notes that may not leave the building, an offline app, or millions of cheap simple requests. API: when you need top quality reasoning or coding, long context, or you don't want to run servers.
</details>

## Learn more (optional)
- Intro to Large Language Models (Karpathy, 1 hour, a must-watch): https://www.youtube.com/watch?v=zjkBMFhNj_g
- Ollama API docs: https://github.com/ollama/ollama/blob/main/docs/api.md
- Ollama model library: https://ollama.com/library

## Next
You've finished Level 6. → [7.1 · Chatbot API with memory in a database](../../level-7-real-world-ai-apps/01-chatbot-api-with-memory-in-a-database)
