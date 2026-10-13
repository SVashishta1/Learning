# 29 · Two AIs: writer and critic

**What it does:** a **team of two**. The writer AI drafts something, the critic AI scores it (1–10) and lists fixes, and the writer improves it. This repeats until the score reaches 8 (or after 3 rounds). You watch the score go up.

## Run it
```bash
cd part-6-ai-agents-and-teams/29-two-ais-writer-and-critic
python writer_and_critic.py
python writer_and_critic.py "A short, friendly email asking my landlord to fix the heating"
```

## The idea in one sentence
Same AI, two different **roles** (system prompts). Having one AI check another's work catches mistakes that a single AI misses in its own writing.

## Try this
1. Make the critic nicer, or much harsher, by editing `CRITIC`. How does that change the number of rounds?
2. Turn it into a "coder and tester" team: the writer writes a Python function, the critic checks it for bugs.
