# 6.5 · Run an open LLM on your laptop

**What you build:** two ways to run a real chat model **on your own machine**, free and private, with no API key:
- **Part A, Ollama:** the easiest way to run Llama, Qwen or Gemma locally, plus a Python chat client with streaming and memory.
- **Part B, transformers:** load a small model yourself and print the **chat template**, the exact text the model sees behind a "chat".

**Like you're 10:** using an API is ordering pizza: fast, great, but you pay each time and the restaurant sees your order. Running locally is cooking at home: you need a kitchen (RAM/GPU), the food may be simpler, but it's free and private.

## Part A: Ollama
1. Install: https://ollama.com/download
2. Download a model: `ollama pull llama3.2:3b` (~2 GB; needs ~8 GB RAM)
3. Chat:
   ```bash
   cd level-6-transformers/05-run-an-open-llm-on-your-laptop
   pip install -r requirements.txt
   python ollama_chat.py               # or: python ollama_chat.py qwen2.5:3b
   ```

## Part B: transformers
```bash
python transformers_chat.py            # downloads SmolLM2-360M (~720 MB)
```

## Key ideas
- **Chat = text completion with a template.** System/user/assistant messages are glued together with special tokens; the model simply continues the text.
- **Streaming:** tokens are sent as they're generated, which feels much faster to users.
- **Memory is just history:** the model is stateless, so *you* resend the whole conversation every turn. (Same with Claude's API in Level 7.)
- **Local vs. API trade-offs:**

| | Local open model | Hosted API (Claude etc.) |
|--|--|--|
| Cost | free after hardware | pay per token |
| Privacy | data never leaves your machine | sent to the provider |
| Quality | good for small tasks | state of the art |
| Speed | depends on your machine | fast, scalable |
| Ops work | you manage it | none |

- **Quantization:** Ollama models are compressed to 4 bits so a 3B-parameter model fits in ~2 GB.

## Your turn
1. Compare 3 local models on the same 5 questions. Note speed (tokens/sec) and quality.
2. Ollama also offers an OpenAI-style API and embeddings (`/api/embed`). Use the embeddings to redo the semantic search from 5.4, fully local.
3. Load the pirate LoRA adapter from 6.3 on top of SmolLM2-135M and chat with it.

## Watch
- Intro to Large Language Models (Karpathy, 1 hour, a must-watch): https://www.youtube.com/watch?v=zjkBMFhNj_g
- Ollama docs: https://github.com/ollama/ollama/blob/main/docs/api.md
