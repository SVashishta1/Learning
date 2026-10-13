# 🚀 AI Engineer Journey: from "Hello API" to multi-agent systems

**52 hands-on projects in 9 levels.** Each one is small enough to finish in an evening and builds on the last, so you gain confidence at every step. Every project folder has its own **README** (what you build, a "like you're 10" explanation, exact run steps, key ideas, "your turn" challenges, and videos to watch), its own `requirements.txt`, and (from Level 1 on, where it makes sense) **tests**.

```
Level 0  Setup ───────────────► your workbench
Level 1  APIs ────────────────► how software talks (every AI product is an API)
Level 2  Neural nets by hand ─► what "learning" really is
Level 3  Classic ML ──────────► the models that still run most businesses
Level 4  Computer vision ─────► CNNs, transfer learning, serving models
Level 5  Text models ─────────► bigrams → RNNs → embeddings → BERT → tokenizers
Level 6  Transformers ────────► attention, mini-GPT, LoRA fine-tuning, local LLMs
Level 7  Real-world AI apps ──► chatbot, extraction, RAG, agents, evals, deployment
Level 8  Multi-agent systems ─► AI teams with tools, routing, review and human approval
```

## The roadmap

### [Level 0 · Setup](level-0-setup)
| # | Project | Time |
|---|---------|------|
| 0.1 | [Set up your AI workbench](level-0-setup/01-setup-your-ai-workbench) | 30 min |
| 0.2 | [Python for AI warm-up (10 exercises)](level-0-setup/02-python-for-ai-warmup) | 1 h |

### [Level 1 · APIs: a restaurant menu for programs](level-1-apis)
| # | Project | Time |
|---|---------|------|
| 1.1 | [Hello API: the waiter says hi](level-1-apis/01-hello-api-the-waiter-says-hi) | 30 min |
| 1.2 | [Calculator API: query parameters + first tests](level-1-apis/02-calculator-api-query-parameters) | 45 min |
| 1.3 | [Joke & quote API: random picks + POST](level-1-apis/03-joke-and-quote-api-random-picks) | 1 h |
| 1.4 | [To-do API: CRUD in memory](level-1-apis/04-todo-api-crud-in-memory) | 1.5 h |
| 1.5 | [To-do API with SQLite, then PostgreSQL](level-1-apis/05-todo-api-with-sqlite-then-postgres) | 2 h |
| 1.6 | [Login API: hashed passwords + JWT](level-1-apis/06-login-api-hashed-passwords-and-jwt) | 2 h |
| 1.7 | [Dockerize & deploy to the cloud](level-1-apis/07-dockerize-and-deploy-to-the-cloud) | 2 h |
| 1.8 | [Weather proxy: calling other APIs (timeouts, retries, caching)](level-1-apis/08-weather-proxy-calling-other-apis) | 1.5 h |

### [Level 2 · Neural nets from scratch: a student learning from mistakes](level-2-neural-nets-from-scratch)
| # | Project | Time |
|---|---------|------|
| 2.1 | [One neuron learns y = 2x (plain Python)](level-2-neural-nets-from-scratch/01-one-neuron-learns-y-equals-2x) | 45 min |
| 2.2 | [Forward pass: two-layer network in NumPy](level-2-neural-nets-from-scratch/02-forward-pass-two-layer-network-numpy) | 1 h |
| 2.3 | [Backprop by hand: learn XOR](level-2-neural-nets-from-scratch/03-backprop-by-hand-learns-xor) | 2 h |
| 2.4 | [Your own mini framework (Layer classes)](level-2-neural-nets-from-scratch/04-mini-framework-layer-classes) | 2 h |
| 2.5 | [Same network in PyTorch: does your math match?](level-2-neural-nets-from-scratch/05-same-network-in-pytorch-compare) | 1 h |
| 2.6 | [Micrograd: build an autograd engine](level-2-neural-nets-from-scratch/06-micrograd-autograd-engine) | 3 h |

### [Level 3 · Classic ML: sorting toys into groups](level-3-classic-ml)
| # | Project | Time |
|---|---------|------|
| 3.1 | [House price predictor (linear regression)](level-3-classic-ml/01-house-price-predictor-linear-regression) | 1 h |
| 3.2 | [Spam detector (logistic regression)](level-3-classic-ml/02-spam-detector-logistic-regression) | 1 h |
| 3.3 | [Iris flower classifier (decision tree)](level-3-classic-ml/03-iris-flower-classifier-decision-tree) | 45 min |
| 3.4 | [Customer groups (k-means)](level-3-classic-ml/04-customer-groups-kmeans-clustering) | 1 h |
| 3.5 | [Model evaluation playground](level-3-classic-ml/05-model-evaluation-playground) | 1.5 h |
| 3.6 | [Churn predictor end to end: pipeline → tuning → API](level-3-classic-ml/06-churn-predictor-end-to-end-pipeline) | 3 h |

### [Level 4 · Computer vision: teaching a computer to see](level-4-computer-vision)
| # | Project | Time |
|---|---------|------|
| 4.1 | [MNIST digits with a simple neural net](level-4-computer-vision/01-mnist-digits-simple-neural-net) | 1 h |
| 4.2 | [Cats vs dogs CNN](level-4-computer-vision/02-cats-vs-dogs-cnn) | 2 h |
| 4.3 | [Transfer learning: ResNet on your own photos](level-4-computer-vision/03-transfer-learning-resnet-on-your-own-photos) | 2 h |
| 4.4 | [Serve it: image classifier behind `/predict`](level-4-computer-vision/04-serve-image-classifier-fastapi) | 1.5 h |
| 4.5 | [Draw-a-digit web app](level-4-computer-vision/05-draw-a-digit-web-app) | 1.5 h |

### [Level 5 · Small text models: teaching a computer to read](level-5-text-models)
| # | Project | Time |
|---|---------|------|
| 5.1 | [Word counter + bag-of-words sentiment (Naive Bayes)](level-5-text-models/01-word-counter-and-bag-of-words-sentiment) | 1 h |
| 5.2 | [Next-letter predictor: bigram name generator](level-5-text-models/02-next-letter-predictor-bigram-name-generator) | 1.5 h |
| 5.3 | [Tiny RNN name generator](level-5-text-models/03-tiny-rnn-name-generator) | 2 h |
| 5.4 | [Embeddings: find similar words and sentences](level-5-text-models/04-embeddings-find-similar-sentences) | 1.5 h |
| 5.5 | [Sentiment with pretrained DistilBERT (+ fine-tuning)](level-5-text-models/05-sentiment-with-pretrained-distilbert) | 2 h |
| 5.6 | [BPE tokenizer from scratch](level-5-text-models/06-bpe-tokenizer-from-scratch) | 2 h |

### [Level 6 · Transformers: a model that pays attention](level-6-transformers)
| # | Project | Time |
|---|---------|------|
| 6.1 | [Self-attention by hand (NumPy)](level-6-transformers/01-self-attention-by-hand-numpy) | 1.5 h |
| 6.2 | [Mini-GPT trained on Shakespeare](level-6-transformers/02-mini-gpt-trained-on-shakespeare) | 4 h |
| 6.3 | [Fine-tune a small LLM with LoRA](level-6-transformers/03-fine-tune-a-small-llm-with-lora) | 2 h |
| 6.4 | [Translator & summariser with Hugging Face](level-6-transformers/04-translator-and-summarizer-with-huggingface) | 1 h |
| 6.5 | [Run an open LLM on your laptop (Ollama)](level-6-transformers/05-run-an-open-llm-on-your-laptop) | 1 h |

### [Level 7 · Real-world AI apps: putting it all together](level-7-real-world-ai-apps)
| # | Project | Time |
|---|---------|------|
| 7.1 | [Chatbot API with memory in a database (+ streaming)](level-7-real-world-ai-apps/01-chatbot-api-with-memory-in-a-database) | 2 h |
| 7.2 | [Structured data extractor: invoices → validated JSON](level-7-real-world-ai-apps/02-structured-data-extractor-invoices-to-json) | 1.5 h |
| 7.3 | [RAG: ask questions about your PDFs](level-7-real-world-ai-apps/03-rag-ask-questions-about-your-pdfs) | 3 h |
| 7.4 | [AI agent with tools (calculator, weather, web search)](level-7-real-world-ai-apps/04-ai-agent-with-tools-calculator-weather-search) | 2 h |
| 7.5 | [Evaluate your RAG and chatbot](level-7-real-world-ai-apps/05-evaluate-your-rag-and-chatbot) | 2 h |
| 7.6 | [Capstone: deploy a full AI app (auth, limits, metrics, CI)](level-7-real-world-ai-apps/06-capstone-deploy-a-full-ai-app) | 4 h |

### [Level 8 · Multi-agent systems: AI teams that get real work done](level-8-multi-agent-systems)
| # | Project | Pattern | Time |
|---|---------|---------|------|
| 8.1 | [Writer + critic reflection loop](level-8-multi-agent-systems/01-writer-and-critic-reflection-loop) | evaluator-optimizer | 1.5 h |
| 8.2 | [Customer-support router + specialists](level-8-multi-agent-systems/02-customer-support-router-and-specialists) | routing, handoffs | 2.5 h |
| 8.3 | [Research team: planner, parallel researchers, writer](level-8-multi-agent-systems/03-research-team-planner-researchers-writer) | orchestrator-workers | 2 h |
| 8.4 | [Data analyst agent: text-to-SQL with a reviewer](level-8-multi-agent-systems/04-data-analyst-agent-text-to-sql) | guardian agent | 2.5 h |
| 8.5 | [Code review crew: parallel reviewers](level-8-multi-agent-systems/05-code-review-crew-parallel-reviewers) | parallelization | 2 h |
| 8.6 | [Build your own MCP server](level-8-multi-agent-systems/06-build-your-own-mcp-server) | Model Context Protocol | 2 h |
| 8.7 | [Human-in-the-loop file organizer](level-8-multi-agent-systems/07-human-in-the-loop-file-organizer-agent) | approvals, sandbox, audit | 2 h |
| 8.8 | [Capstone: AI incident-response team](level-8-multi-agent-systems/08-capstone-ai-incident-response-team) | full multi-agent workflow | 4 h |

## How to use this repo
1. **Go in order.** Each level reuses ideas from the one before. Finish a level's last project before moving on.
2. **Run it → read it → break it → extend it.** Run the project, read every line (comments explain the *why*), change something to see what breaks, then do the **Your turn** challenges. The challenges are where the learning sticks.
3. **Build it yourself, then with the library.** Levels 2, 3, 5 and 6 deliberately show the from-scratch version next to the library version.
4. **Watch the linked video** when a concept feels fuzzy. Each README lists the best free ones.
5. **Commit after every project.** Your GitHub history becomes your portfolio.
6. **Pace:** ~1 project per evening ≈ 3 months part-time. Don't rush Levels 2 and 6; they're what separate engineers who *use* AI from engineers who *understand* it.

## What you need
| From | Need | Cost |
|------|------|------|
| Level 0 | Python 3.11+, Git, VS Code | free |
| Level 1.5+ | Docker Desktop | free |
| Levels 4–6 | PyTorch; a GPU is optional (Google Colab has free GPUs) | free |
| Levels 7–8 | an **Anthropic API key** from https://platform.claude.com | a few dollars total; use `CLAUDE_MODEL=claude-haiku-5-5` to keep it very cheap |
| Level 6.5 | Ollama, for local LLMs | free |

Every Level 7–8 project has **tests that use a fake LLM**, so `pytest` runs free and offline even without a key.

## Turn this into a job
- **Portfolio:** pin 4 repos/projects on your GitHub: the churn API (3.6), the RAG capstone (7.6), the support team (8.2) and the incident responder (8.8). Each needs a README with a GIF or 2-minute video demo.
- **Talk about trade-offs** in interviews: RAG vs. fine-tuning (7.3 / 6.3), cost vs. quality (7.5), when to use an agent vs. a fixed workflow (Level 8), how you keep agents safe (8.7).
- **The skills employers ask for in 2026** are all here: Python, APIs, SQL, Docker, PyTorch, transformers, embeddings and RAG, evals, agents and tool use, MCP, deployment and monitoring.

## Free courses that pair well with this repo
- Karpathy, *Neural Networks: Zero to Hero*: https://www.youtube.com/playlist?list=PLAqhIrjkxbuWI23v9cThsA9GvCAUhRvKZ
- 3Blue1Brown, *Neural networks*: https://www.youtube.com/playlist?list=PLZHQObOWTQDNU6R1_67000Dx_ZCJB-3pi
- fast.ai, *Practical Deep Learning for Coders*: https://course.fast.ai/
- Hugging Face, *LLM course*: https://huggingface.co/learn/llm-course/chapter1/1
- Anthropic courses (prompting, tool use, RAG): https://github.com/anthropics/courses
- Made With ML (MLOps): https://madewithml.com/

> Videos linked as `youtube.com/results?search_query=...` open a YouTube search with the named video at the top, so the link keeps working even if a video is re-uploaded.
