"""Ask API: a tiny RAG-style AI service with the three pillars of observability built in.

  1. LOGS    -> one JSON object per line on stdout (Docker collects them)
  2. METRICS -> counters and histograms at GET /metrics (Prometheus scrapes them)
  3. TRACES  -> spans for "ask", "retrieve" and the LLM call, sent to Jaeger with OpenTelemetry

FAKE_LLM=1 (the default) answers with a fake model: no API key, no cost.
FAKE_LLM=0 calls Claude (needs ANTHROPIC_API_KEY; CLAUDE_MODEL picks the model).
"""

import json
import logging
import os
import random
import sys
import time
from datetime import datetime, timezone

from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import Response
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.http.trace_exporter import OTLPSpanExporter
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor
from prometheus_client import CONTENT_TYPE_LATEST, Counter, Histogram, generate_latest
from pydantic import BaseModel, Field

SERVICE_NAME = os.getenv("SERVICE_NAME", "ask-api")
FAKE_LLM = os.getenv("FAKE_LLM", "1") == "1"
MODEL = "fake-llm" if FAKE_LLM else os.getenv("CLAUDE_MODEL", "claude-opus-5-5")
FAKE_ERROR_RATE = float(os.getenv("FAKE_ERROR_RATE", "0.05"))  # 5 % of fake calls fail, so graphs show errors


# ---------- 1. LOGS: structured JSON, one line per event ----------
class JsonFormatter(logging.Formatter):
    """Turn a log record into one line of JSON that machines can search and filter."""

    def format(self, record: logging.LogRecord) -> str:
        entry = {
            "time": datetime.now(timezone.utc).isoformat(timespec="milliseconds"),
            "level": record.levelname,
            "service": SERVICE_NAME,
            "message": record.getMessage(),
        }
        entry.update(getattr(record, "fields", {}))  # extra key=value pairs from log_event()
        span_context = trace.get_current_span().get_span_context()
        if span_context.is_valid:  # inside a trace: add its id, so a log line leads to its trace
            entry["trace_id"] = format(span_context.trace_id, "032x")
        return json.dumps(entry)


handler = logging.StreamHandler(sys.stdout)
handler.setFormatter(JsonFormatter())
log = logging.getLogger(SERVICE_NAME)
log.addHandler(handler)
log.setLevel(logging.INFO)
log.propagate = False  # don't print every line twice through uvicorn's own logger


def log_event(message: str, level: int = logging.INFO, **fields) -> None:
    log.log(level, message, extra={"fields": fields})


# ---------- 2. METRICS: numbers Prometheus collects every few seconds ----------
# Labels (the list in the brackets) split one metric into several lines, e.g. one per status code.
REQUESTS = Counter("http_requests_total", "HTTP requests handled", ["method", "path", "status"])
REQUEST_SECONDS = Histogram("http_request_duration_seconds", "Time to answer an HTTP request", ["path"])
LLM_SECONDS = Histogram(
    "llm_request_duration_seconds",
    "Time the language model took to answer",
    ["model"],
    buckets=(0.1, 0.25, 0.5, 1, 2, 5, 10, 30),  # the "boxes" a duration is sorted into
)
LLM_TOKENS = Counter("llm_tokens_total", "Tokens sent to and received from the model", ["model", "direction"])
LLM_ERRORS = Counter("llm_errors_total", "Failed model calls", ["model", "reason"])


# ---------- 3. TRACES: a timeline of every step inside one request ----------
provider = TracerProvider(resource=Resource.create({"service.name": SERVICE_NAME}))
if os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"):  # e.g. http://jaeger:4318 (set in compose.yaml)
    # The exporter reads the address from that variable and sends spans to <address>/v1/traces.
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
trace.set_tracer_provider(provider)
tracer = trace.get_tracer(SERVICE_NAME)


# ---------- The tiny "knowledge base" and the AI part ----------
DOCS = [
    {"id": "refunds", "text": "Customers can get a full refund within 30 days of purchase."},
    {"id": "shipping", "text": "Standard shipping takes 3 to 5 working days. Express takes 1 day."},
    {"id": "warranty", "text": "Every bike has a 2 year warranty on the frame and 1 year on parts."},
    {"id": "support", "text": "Support is open Monday to Friday, 9:00 to 17:00, by chat or email."},
]


def retrieve(question: str, top_k: int = 2) -> list[dict]:
    """Score each document by how many question words it contains; keep the best top_k."""
    words = {w.strip("?.,!").lower() for w in question.split() if len(w) > 2}
    scored = [(sum(w in doc["text"].lower() for w in words), doc) for doc in DOCS]
    scored.sort(key=lambda pair: pair[0], reverse=True)
    return [doc for score, doc in scored[:top_k] if score > 0]


def fake_llm(prompt: str) -> tuple[str, int, int]:
    """Pretend to be a model: wait a bit, sometimes fail, count tokens roughly (1 token ~ 4 chars)."""
    time.sleep(random.uniform(0.2, 1.2))
    if random.random() < FAKE_ERROR_RATE:
        raise RuntimeError("fake model overloaded")
    answer = "Based on our documents: " + prompt.split("Documents:\n", 1)[-1].split("\n")[0]
    return answer, len(prompt) // 4, len(answer) // 4


def claude_llm(prompt: str) -> tuple[str, int, int]:
    """Call Claude through the official Anthropic SDK and return (text, input tokens, output tokens)."""
    import anthropic  # imported here so FAKE_LLM=1 works without the package configured

    extra = {}
    if MODEL in {"claude-opus-5-5", "claude-opus-5", "claude-fable-5-1", "claude-sonnet-5-5"}:
        # If a safety check ever declines a request, the API retries it on a fallback model.
        extra = {"betas": ["server-side-fallback-2026-07-01"], "fallbacks": "default"}
    response = anthropic.Anthropic().beta.messages.create(
        model=MODEL, max_tokens=1000, messages=[{"role": "user", "content": prompt}], **extra
    )
    if response.stop_reason == "refusal":
        raise RuntimeError("the model declined this request")
    text = "".join(block.text for block in response.content if block.type == "text")
    return text, response.usage.input_tokens, response.usage.output_tokens


def call_llm(prompt: str) -> str:
    """Call the model inside its own span, and record time, tokens and errors as metrics."""
    # Span name and attribute names follow OpenTelemetry's "GenAI" conventions, so tools understand them.
    with tracer.start_as_current_span(f"chat {MODEL}") as span:
        span.set_attribute("gen_ai.operation.name", "chat")
        span.set_attribute("gen_ai.provider.name", "fake" if FAKE_LLM else "anthropic")
        span.set_attribute("gen_ai.request.model", MODEL)
        start = time.perf_counter()
        try:
            text, tokens_in, tokens_out = (fake_llm if FAKE_LLM else claude_llm)(prompt)
        except Exception as error:
            LLM_ERRORS.labels(MODEL, type(error).__name__).inc()
            span.record_exception(error)
            span.set_status(trace.Status(trace.StatusCode.ERROR, str(error)))
            raise
        finally:
            LLM_SECONDS.labels(MODEL).observe(time.perf_counter() - start)
        LLM_TOKENS.labels(MODEL, "input").inc(tokens_in)
        LLM_TOKENS.labels(MODEL, "output").inc(tokens_out)
        span.set_attribute("gen_ai.usage.input_tokens", tokens_in)
        span.set_attribute("gen_ai.usage.output_tokens", tokens_out)
        return text


# ---------- The web API ----------
# Recent FastAPI versions create a span for every request ("POST /ask") on their own once a
# tracer provider exists. We keep those, skip the tiny inner FastAPI steps, and skip the
# /metrics and /health calls that Prometheus and Docker make every few seconds (pure noise).
app = FastAPI(
    title="Ask API (observable)",
    telemetry={
        "operation_spans": False,
        "exclude": lambda scope: scope.get("path") in ("/metrics", "/health"),
    },
)


@app.middleware("http")
async def measure(request: Request, call_next):
    """Runs around EVERY request: time it and count it by path and status code."""
    start = time.perf_counter()
    response = await call_next(request)
    route = request.scope.get("route")
    # Use the route template ("/ask"), never the raw URL, so labels stay few (low "cardinality").
    path = route.path if route else "unknown"
    REQUESTS.labels(request.method, path, str(response.status_code)).inc()
    REQUEST_SECONDS.labels(path).observe(time.perf_counter() - start)
    return response


class AskIn(BaseModel):
    question: str = Field(min_length=3, max_length=500)


@app.get("/health")
def health():
    return {"status": "ok", "model": MODEL}


@app.get("/metrics")
def metrics():
    # The text format Prometheus understands: "# HELP", "# TYPE", then name{labels} value.
    return Response(generate_latest(), media_type=CONTENT_TYPE_LATEST)


@app.post("/ask")
def ask(body: AskIn):
    with tracer.start_as_current_span("ask") as span:
        start = time.perf_counter()
        with tracer.start_as_current_span("retrieve") as retrieve_span:
            docs = retrieve(body.question)
            retrieve_span.set_attribute("retrieve.documents", len(docs))
        context = "\n".join(doc["text"] for doc in docs) or "No matching documents."
        prompt = f"Answer the question using only these documents.\nDocuments:\n{context}\n\nQuestion: {body.question}"
        try:
            answer = call_llm(prompt)
        except Exception as error:
            # Log WHAT happened and the ids needed to find it, never the user's full text or secrets.
            log_event("llm call failed", logging.ERROR, error=str(error), question_chars=len(body.question))
            raise HTTPException(status_code=502, detail="The language model failed. Please try again.")
        duration_ms = round((time.perf_counter() - start) * 1000)
        log_event(
            "answered",
            question_chars=len(body.question),
            sources=[doc["id"] for doc in docs],
            duration_ms=duration_ms,
            model=MODEL,
        )
        span.set_attribute("ask.sources", len(docs))
        trace_id = format(span.get_span_context().trace_id, "032x")
        return {"answer": answer, "sources": [doc["id"] for doc in docs], "trace_id": trace_id}
