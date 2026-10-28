"""benchmark.py: measure what each optimisation saves on the same 12 questions, then time streaming.

python benchmark.py --simulate     # free: a simulated model with made-up but realistic speeds and token counts
python benchmark.py                # the real thing (Claude, costs a few cents; set CLAUDE_MODEL / CHEAP_MODEL to compare)
"""
import argparse
import statistics
import tempfile
import time
from pathlib import Path

import cost_tools
import llm

QUESTIONS = [
    "What's the cut-off time for Express?",
    "How much is Saturday delivery?",
    "Which form do I use for a damage claim?",
    "whats the CUT-OFF time for express",                   # same as question 1, written differently
    "Do service credits expire?",
    "My Express parcel to Inverness was collected on Friday at 16:00 and arrived on Tuesday. Was it late, and what do I get?",
    "How much does a redirection cost after dispatch?",
    "How much is Saturday delivery?",                       # exact repeat
    "Our chilled pharma parcel had a 45-minute temperature excursion and arrived after 30 hours. What are our options?",
    "How cold is the Frozen range?",
    "We were charged twice and the parcel was also damaged. What should we do first and how long will each take?",
    "Which form do I use for a damage claim?",              # exact repeat
]


# ---------------- A simulated model, so the benchmark runs free ----------------
class SimulatedClaude:
    """Pretends to be the API: realistic token counts and waits (NOT real measurements).
    Assumptions: Opus-class waits 0.5 s + 10 ms per output token; Haiku-class 0.2 s + 3 ms per token;
    a prompt-cache hit trims 30% off the start-up wait; cache entries live 5 minutes."""
    SPEED = {"strong": (0.5, 0.010), "cheap": (0.2, 0.003)}

    def __init__(self):
        from fake_llm import FakeClaude
        self._fake = FakeClaude(responder=self._respond)
        self.beta, self.messages = self._fake.beta, self._fake.messages
        self.beta.messages.stream = self._stream
        self.cache: dict[tuple, float] = {}

    def _kind(self, model):
        return "cheap" if "haiku" in model else "strong"

    @staticmethod
    def _hard(question: str) -> bool:
        return len(question) > 90 or " and " in question.lower()

    def _respond(self, request, sleep=True):
        from fake_llm import json_reply, text_reply
        system = request["system"][0]
        question = request["messages"][-1]["content"]
        sys_tokens, q_tokens = cost_tools.estimate_tokens(system["text"]), cost_tools.estimate_tokens(question)
        read = write = 0
        if "cache_control" in system:
            key = (request["model"], system["text"])
            if time.time() - self.cache.get(key, -1e9) < 300:
                read = sys_tokens
            else:
                write = sys_tokens
            self.cache[key] = time.time()
        base, per_token = self.SPEED[self._kind(request["model"])]
        if "format" in request.get("output_config", {}):                  # the router's classification
            out_tokens, reply = 8, json_reply({"level": "hard" if self._hard(question) else "easy"})
        else:
            out_tokens = 110 if self._hard(question) else 45
            reply = text_reply(" ".join(["(simulated answer)"] + ["word"] * (out_tokens - 3)))
        reply.usage.input_tokens = sys_tokens + q_tokens - read - write
        reply.usage.output_tokens, reply.usage.cache_read_input_tokens = out_tokens, read
        reply.usage.cache_creation_input_tokens = write
        if sleep:
            time.sleep(base * (0.7 if read else 1.0) + out_tokens * per_token)
        return reply

    def _stream(self, **request):
        reply = self._respond(request, sleep=False)
        base, per_token = self.SPEED[self._kind(request["model"])]
        words = reply.content[0].text.split(" ")

        class _Live:
            def __enter__(s): return s
            def __exit__(s, *exc): return False
            @property
            def text_stream(s):
                time.sleep(base)                                          # waiting for the first token
                for i, w in enumerate(words):
                    yield w if i == 0 else " " + w
                    time.sleep(per_token)
        return _Live()


# ---------------- The four setups ----------------
def run_setup(name: str, use_prompt_cache: bool, use_response_cache: bool, use_routing: bool) -> dict:
    cache = cost_tools.ResponseCache(str(Path(tempfile.mkdtemp()) / "cache.db")) if use_response_cache else None
    costs, latencies, models = [], [], []
    for q in QUESTIONS:
        start, cost, model = time.perf_counter(), 0.0, llm.MODEL
        if use_routing:
            model, router_reply = cost_tools.route(q)
            cost += router_reply.cost_usd
        hit = cache.get(model, cost_tools.SYSTEM, q) if cache else None
        if hit is None:
            reply = cost_tools.answer(q, model=model, cache=use_prompt_cache)
            cost += reply.cost_usd
            if cache:
                cache.put(model, cost_tools.SYSTEM, q, reply.text)
        else:
            model = "response cache"
        costs.append(cost)
        latencies.append(time.perf_counter() - start)
        models.append(model)
    p95 = sorted(latencies)[max(0, round(0.95 * len(latencies)) - 1)]
    return {"name": name, "total": sum(costs), "mean": statistics.mean(latencies), "p95": p95,
            "per_1000": sum(costs) / len(costs) * 1000, "models": models}


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--simulate", action="store_true", help="use the simulated model (free)")
    args = parser.parse_args()
    if args.simulate:
        llm.set_client(SimulatedClaude())
        print("(SIMULATED model: token counts and waits follow the assumptions in SimulatedClaude, not real API calls)\n")
    print(f"Strong model: {llm.MODEL}   cheap model: {llm.CHEAP_MODEL}   handbook ≈ "
          f"{cost_tools.estimate_tokens(cost_tools.SYSTEM)} tokens   {len(QUESTIONS)} questions\n")
    setups = [("1 strong model only", False, False, False),
              ("2 + prompt caching", True, False, False),
              ("3 + response cache", True, True, False),
              ("4 + routing", True, True, True)]
    print(f"{'setup':22s} {'total $':>9s} {'$ / 1000 q':>10s} {'mean s':>7s} {'p95 s':>6s}  $/month at 5,000 q/day")
    results = []
    for name, *flags in setups:
        r = run_setup(name, *flags)
        results.append(r)
        print(f"{r['name']:22s} {r['total']:9.4f} {r['per_1000']:10.2f} {r['mean']:7.2f} {r['p95']:6.2f}  "
              f"{r['per_1000'] * 150:10,.0f}")
    routed = results[-1]["models"]
    print(f"\nWho answered in setup 4: {routed.count(llm.CHEAP_MODEL)} cheap, {routed.count(llm.MODEL)} strong, "
          f"{routed.count('response cache')} from the response cache")

    print("\nStreaming (one hard question):")
    start = time.perf_counter()
    first = None
    for piece in llm.stream(QUESTIONS[5], system=cost_tools.SYSTEM, max_tokens=400):
        first = first or time.perf_counter() - start
    total = time.perf_counter() - start
    print(f"  time to first token {first:.2f} s, full answer {total:.2f} s -> the user starts reading "
          f"{total - first:.2f} s sooner")


if __name__ == "__main__":
    main()
