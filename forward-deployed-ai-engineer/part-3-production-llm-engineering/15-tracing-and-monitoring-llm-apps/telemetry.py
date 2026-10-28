"""telemetry.py: switch on OpenTelemetry tracing once, and send spans where you want them.

  console  print every span as JSON in the terminal (a first look)
  jaeger   send spans over OTLP to a local Jaeger (http://localhost:16686 to look at them)
  file     append one JSON line per span to traces.jsonl (monitor.py reads it to raise alerts)
Several at once: setup("console,file").
"""
import json
from pathlib import Path

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (BatchSpanProcessor, ConsoleSpanExporter, SimpleSpanProcessor,
                                            SpanExporter, SpanExportResult)

SERVICE = "northwind-assistant"
TRACE_FILE = Path(__file__).with_name("traces.jsonl")


class JsonlSpanExporter(SpanExporter):
    """Writes each finished span as one line of JSON: a tiny local 'trace store'."""
    def __init__(self, path: Path = TRACE_FILE):
        self.path = path

    def export(self, spans) -> SpanExportResult:
        with self.path.open("a", encoding="utf-8") as f:
            for s in spans:
                ctx = s.get_span_context()
                f.write(json.dumps({
                    "trace_id": format(ctx.trace_id, "032x"), "span_id": format(ctx.span_id, "016x"),
                    "parent_id": format(s.parent.span_id, "016x") if s.parent else None,
                    "name": s.name, "start": s.start_time / 1e9, "duration_ms": round((s.end_time - s.start_time) / 1e6, 1),
                    "status": s.status.status_code.name, "attributes": dict(s.attributes),
                    "events": [e.name for e in s.events]}) + "\n")
        return SpanExportResult.SUCCESS

    def shutdown(self):
        pass


def setup(exporters: str = "console") -> TracerProvider:
    """Call once at start-up, BEFORE the first span. Returns the provider (call .shutdown() at the end to flush)."""
    provider = TracerProvider(resource=Resource.create({"service.name": SERVICE}))   # the name you'll see in Jaeger
    for name in exporters.split(","):
        if name == "console":
            provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))
        elif name == "file":
            provider.add_span_processor(SimpleSpanProcessor(JsonlSpanExporter()))
        elif name == "jaeger":
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
            # Batch = send spans in groups in the background (what you use in production).
            provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter(endpoint="localhost:4317", insecure=True)))
        elif name != "none":
            raise ValueError(f"unknown exporter {name!r}: use console, jaeger, file or none")
    trace.set_tracer_provider(provider)
    return provider


tracer = trace.get_tracer("northwind.assistant")
