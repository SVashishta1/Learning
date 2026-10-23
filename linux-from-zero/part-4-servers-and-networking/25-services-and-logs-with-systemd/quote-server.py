#!/usr/bin/env python3
"""quote-server.py - a tiny web service that hands out AI quotes as JSON.

It uses only Python's standard library (nothing to pip install), so it is perfect
for practising how to run a program as a systemd service.

Endpoints:
  GET /        -> {"quote": "...", "served_by": "...", "pid": 1234}
  GET /health  -> {"status": "ok"}
Settings come from environment variables (systemd sets them from the unit file):
  PORT      which port to listen on (default 8077)
  GREETING  a word added to every reply (default "Hello")
"""
import json
import os
import random
import signal
import sys
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

PORT = int(os.environ.get("PORT", "8077"))          # read the port from the environment
GREETING = os.environ.get("GREETING", "Hello")      # and the greeting

QUOTES = [
    "A model is only as good as its data.",
    "Log everything; you will need it at 2 a.m.",
    "Small models, fast answers, happy users.",
    "If it is not monitored, it is not in production.",
    "Restart on failure, then find out why it failed.",
]


def log(message):
    """Print a line and flush at once, so systemd's journal gets it immediately."""
    print(message, flush=True)


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):                                # called for every GET request
        if self.path == "/health":
            body = {"status": "ok"}
        elif self.path == "/":
            body = {
                "greeting": GREETING,
                "quote": random.choice(QUOTES),
                "served_by": os.environ.get("USER") or str(os.getuid()),
                "pid": os.getpid(),
            }
        else:
            self.send_error(404, "Not found")
            return
        data = json.dumps(body).encode()             # dict -> JSON text -> bytes
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, fmt, *args):               # one log line per request, to stdout
        log(f"{self.client_address[0]} {fmt % args}")


def stop(signum, frame):
    """systemctl stop sends SIGTERM: say goodbye nicely, then exit with code 0."""
    log(f"Got signal {signum}, shutting down cleanly")
    sys.exit(0)


if __name__ == "__main__":
    signal.signal(signal.SIGTERM, stop)              # run stop() when SIGTERM arrives
    server = ThreadingHTTPServer(("127.0.0.1", PORT), Handler)
    log(f"quote-server starting on http://127.0.0.1:{PORT} (pid {os.getpid()})")
    server.serve_forever()                           # wait for visitors, forever
