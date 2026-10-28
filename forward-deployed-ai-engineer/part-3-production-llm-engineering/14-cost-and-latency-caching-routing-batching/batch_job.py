"""batch_job.py: the nightly "summarise yesterday's tickets" job, sent as ONE Message Batches request (half price).

python batch_job.py                 # build batch_requests.jsonl and compare the cost: normal calls vs batch (free)
python batch_job.py --submit        # send it (needs a key); prints the batch id
python batch_job.py --collect ID    # check on it; when it has ended, save batch_results.jsonl
"""
import argparse
import json
import random

import cost_tools
import llm

TEMPLATES = ["Parcel {id} is {d} days late and the customer wants an update.",
             "Customer reports {id} arrived with a crushed box and broken bottles.",
             "Invoice for {id} was charged twice, customer asks for a refund.",
             "Customer wants to redirect {id} to their new warehouse.",
             "Chilled shipment {id} had a temperature excursion of {d}0 minutes."]


def make_tickets(n: int = 200, seed: int = 7) -> list[dict]:
    rng = random.Random(seed)                                   # same tickets every run
    return [{"id": f"T-{5000 + i}", "text": rng.choice(TEMPLATES).format(id=f"NW-{rng.randint(10000, 99999)}",
                                                                         d=rng.randint(1, 6))} for i in range(n)]


def estimate(requests: list[dict]) -> dict:
    model = requests[0]["params"]["model"]
    inp = sum(cost_tools.estimate_tokens(r["params"]["system"] + r["params"]["messages"][0]["content"])
              for r in requests)
    out = 60 * len(requests)                                    # assume ~60 output tokens per summary
    normal = llm.cost_usd(model, inp, out)
    return {"model": model, "input_tokens": inp, "output_tokens": out, "normal": normal,
            "batch": normal * cost_tools.BATCH_DISCOUNT}


def main():
    p = argparse.ArgumentParser()
    p.add_argument("--submit", action="store_true")
    p.add_argument("--collect", metavar="BATCH_ID")
    args = p.parse_args()
    client = None
    if args.collect:
        client = llm.claude_client()
        batch = client.messages.batches.retrieve(args.collect)
        counts = batch.request_counts
        print(f"Batch {batch.id}: {batch.processing_status} (succeeded {counts.succeeded}, errored {counts.errored}, "
              f"processing {counts.processing})")
        if batch.processing_status == "ended":
            rows = []
            for item in client.messages.batches.results(args.collect):     # results come in ANY order
                if item.result.type == "succeeded":
                    text = "".join(b.text for b in item.result.message.content if b.type == "text")
                    rows.append({"ticket": item.custom_id, "summary": text})
                else:
                    rows.append({"ticket": item.custom_id, "error": item.result.type})
            cost_tools.save_jsonl(sorted(rows, key=lambda r: r["ticket"]), "batch_results.jsonl")
            print(f"Saved {len(rows)} results to batch_results.jsonl")
        return

    requests = cost_tools.batch_requests(make_tickets())
    cost_tools.save_jsonl(requests, "batch_requests.jsonl")
    e = estimate(requests)
    print(f"Built {len(requests)} requests -> batch_requests.jsonl (model {e['model']})")
    print(f"Estimated tokens: {e['input_tokens']:,} in, {e['output_tokens']:,} out")
    print(f"One call at a time: ${e['normal']:.4f}   as a batch: ${e['batch']:.4f}   (results within 24 h, usually < 1 h)")
    print(f"First request:\n{json.dumps(requests[0], indent=1, ensure_ascii=False)[:600]}")
    if args.submit:
        client = llm.claude_client()
        batch = client.messages.batches.create(requests=requests)
        print(f"\nSubmitted batch {batch.id}, status {batch.processing_status}. "
              f"Later: python batch_job.py --collect {batch.id}")


if __name__ == "__main__":
    main()
