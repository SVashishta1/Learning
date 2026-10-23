"""app.py: a small Northwind assistant where every step is traced: question -> tool -> retrieval -> LLM -> answer.

python app.py "Where is NW-58213?" --offline                       # print the spans in the terminal
python app.py "Where is NW-58213?" --offline --exporter jaeger     # send them to Jaeger (see README)
python app.py --simulate 60 --offline --exporter file              # fake a busy hour -> traces.jsonl
python app.py --simulate 60 --offline --exporter file --incident   # ...during an incident (errors, slowness)
"""
import argparse
import hashlib
import random
import re
import time

from opentelemetry import trace
from opentelemetry.trace import SpanKind, Status, StatusCode

import llm
import safe_log
import telemetry
from telemetry import tracer

KNOWLEDGE = {
    "express": "Express is delivered the next working day by 17:00 when collected before the 15:00 cut-off.",
    "saturday": "Saturday delivery is available for Express only, for £9.50 per parcel.",
    "lost": "A shipment is declared lost after 10 working days with no tracking scan.",
    "claims": "Damage claims use form CL-7 in the customer portal, with photos.",
    "credits": "Service credits expire after 12 months.",
    "redirect": "After dispatch, a redirection costs £6 and adds one working day.",
}
SHIPMENTS = {"NW-58213": "delayed at Leeds hub, re-delivery booked for Friday",
             "NW-60417": "delivered on Tuesday at 10:42"}
STOP = {"a", "an", "the", "is", "are", "my", "i", "do", "does", "for", "to", "of", "in", "on", "what", "where",
        "when", "which", "how", "can", "much", "s", "nw", "after", "with", "and", "per", "be"}
SYSTEM = ("You are Northwind Logistics' assistant. Answer in 1-2 sentences using only the <context>. "
          "If it doesn't answer the question, say \"I don't know, please contact support.\"")


# ---------- each step gets its own span ----------
def retrieve(question: str, k: int = 2) -> list[str]:
    with tracer.start_as_current_span("retrieve") as span:
        words = set(re.findall(r"[a-z]+", question.lower())) - STOP
        scored = sorted(((len(words & set(re.findall(r"[a-z]+", text.lower()))) + 3 * (key in words), key)
                         for key, text in KNOWLEDGE.items()), reverse=True)
        hits = [key for score, key in scored[:k] if score > 0]
        span.set_attribute("retrieval.top_k", k)
        span.set_attribute("retrieval.doc_ids", hits)             # IDs, not text: small and safe
        span.set_attribute("retrieval.best_score", scored[0][0])
        if not hits:
            span.add_event("no documents matched")
        return [KNOWLEDGE[key] for key in hits]


def get_shipment(shipment_id: str) -> str:
    with tracer.start_as_current_span("tool get_shipment", kind=SpanKind.CLIENT) as span:
        span.set_attribute("tool.name", "get_shipment")
        span.set_attribute("tool.shipment_id", shipment_id)
        if shipment_id not in SHIPMENTS:
            raise LookupError(f"unknown shipment {shipment_id}")
        return SHIPMENTS[shipment_id]


def traced_chat(prompt: str, system: str) -> llm.Reply:
    """Wraps llm.chat in a span named like the OpenTelemetry GenAI conventions: 'chat <model>'."""
    model = llm.MODEL if llm.PROVIDER == "claude" else llm.OLLAMA_MODEL
    with tracer.start_as_current_span(f"chat {model}", kind=SpanKind.CLIENT) as span:
        span.set_attribute("gen_ai.operation.name", "chat")
        span.set_attribute("gen_ai.system", "anthropic" if llm.PROVIDER == "claude" else "ollama")
        span.set_attribute("gen_ai.request.model", model)
        for key, value in safe_log.content_fields("gen_ai.prompt", prompt).items():
            span.set_attribute(key, value)                        # fingerprint always; text only if LOG_CONTENT=1
        reply = llm.chat(prompt, system=system, effort="low", max_tokens=300)
        span.set_attribute("gen_ai.usage.input_tokens", reply.input_tokens)
        span.set_attribute("gen_ai.usage.output_tokens", reply.output_tokens)
        span.set_attribute("gen_ai.usage.cache_read_input_tokens", reply.cache_read_tokens)
        span.set_attribute("gen_ai.response.finish_reasons", [reply.stop_reason])
        span.set_attribute("app.cost_usd", round(reply.cost_usd, 6))
        return reply


def handle(question: str, user_id: str) -> str:
    """The root span: everything that happens for one question hangs underneath it."""
    with tracer.start_as_current_span("handle_question", kind=SpanKind.SERVER) as span:
        span.set_attribute("app.user", hashlib.sha256(user_id.encode()).hexdigest()[:10])   # pseudonymous
        for key, value in safe_log.content_fields("app.question", question).items():
            span.set_attribute(key, value)
        trace_id = format(span.get_span_context().trace_id, "032x")
        start = time.perf_counter()
        try:
            context = []
            for shipment_id in re.findall(r"NW-\d{5}", question):
                try:
                    context.append(f"Shipment {shipment_id}: {get_shipment(shipment_id)}")
                except LookupError as e:                         # a handled problem: note it, carry on
                    trace.get_current_span().add_event("tool error", {"error": str(e)})
                    context.append(f"Shipment {shipment_id}: not found")
            context += retrieve(question)
            reply = traced_chat("<context>\n" + "\n".join(context) + f"\n</context>\n\n{question}", SYSTEM)
            idk = "don't know" in reply.text.lower()
            span.set_attribute("app.answer.idk", idk)
            safe_log.log("answered", trace_id=trace_id, user=span.attributes["app.user"], idk=idk,
                         ms=round((time.perf_counter() - start) * 1000), cost_usd=round(reply.cost_usd, 6),
                         **safe_log.content_fields("question", question))
            return reply.text
        except Exception as e:
            span.record_exception(e)                            # stack trace stored on the span
            span.set_status(Status(StatusCode.ERROR, str(e)))
            safe_log.log("failed", 40, trace_id=trace_id, error=type(e).__name__)
            return "Sorry, something went wrong. Please try again."


# ---------- an offline stand-in model with realistic hiccups ----------
def make_offline_responder(incident: bool = False, seed: int = 1):
    """NOT a real model: answers from the context, and is sometimes slow or failing (more so in an 'incident')."""
    from fake_llm import text_reply
    rng = random.Random(seed)

    def respond(request):
        prompt = request["messages"][-1]["content"]
        if rng.random() < (0.25 if incident else 0.02):
            raise RuntimeError("Overloaded (simulated 529 from the model provider)")
        time.sleep(rng.uniform(2.5, 5.0) if incident and rng.random() < 0.5 else rng.uniform(0.05, 0.25))
        lines = re.search(r"<context>\n(.*?)\n</context>", prompt, re.S).group(1).strip().splitlines()
        answer = lines[0] if lines and lines[0] else "I don't know, please contact support."
        return text_reply(answer, input_tokens=len(prompt + request["system"][0]["text"]) // 4,
                          output_tokens=len(answer) // 4)
    return respond


SAMPLE_QUESTIONS = ["Where is NW-58213?", "How much is Saturday delivery?", "When is a parcel lost?",
                    "Which form for damage claims?", "Do service credits expire?", "Where is NW-99999?",
                    "What's the Express cut-off?", "Can I pay in bitcoin?", "How much is a redirect?"]


def main():
    p = argparse.ArgumentParser()
    p.add_argument("question", nargs="?")
    p.add_argument("--offline", action="store_true")
    p.add_argument("--exporter", default="console", help="console, jaeger, file, none (comma-separated)")
    p.add_argument("--simulate", type=int, metavar="N", help="send N sample questions")
    p.add_argument("--incident", action="store_true", help="with --offline: more errors and slow replies")
    args = p.parse_args()
    provider = telemetry.setup(args.exporter)
    if args.offline:
        from fake_llm import FakeClaude
        llm.set_client(FakeClaude(responder=make_offline_responder(args.incident)))
    if args.simulate:
        rng = random.Random(2)
        for i in range(args.simulate):
            handle(rng.choice(SAMPLE_QUESTIONS), user_id=f"user-{rng.randint(1, 12)}")
        print(f"Sent {args.simulate} questions" + (" (incident mode)" if args.incident else ""))
    else:
        print("ANSWER:", handle(args.question or "Where is NW-58213?", user_id="user-1"))
    provider.shutdown()                                         # flush spans still waiting in the batch


if __name__ == "__main__":
    main()
