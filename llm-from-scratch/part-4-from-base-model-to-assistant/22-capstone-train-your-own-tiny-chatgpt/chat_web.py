"""Capstone stage 5b: a ChatGPT-style web page for your model, using only Python's standard library.

python chat_web.py             # then open http://localhost:8000 in your browser
python chat_web.py --port 8080

GET  /       -> the chat page (HTML + a little JavaScript)
POST /chat   -> {"messages": [{"role": "user", "content": "Hi"}, ...]}  ->  {"reply": "..."}
"""
import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from threading import Lock

from common import load_model, load_tokenizer, reply

p = argparse.ArgumentParser()
p.add_argument("--port", type=int, default=8000)
p.add_argument("--host", default="127.0.0.1", help="127.0.0.1 = only this computer can open the page")
p.add_argument("--model", default="chat.pt")
args = p.parse_args()
tok = load_tokenizer()
model = load_model(args.model)
lock = Lock()                     # one generation at a time: the model is not shared safely between threads

PAGE = """<!doctype html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>TinyChat</title>
<style>
  :root { --bg: #f7f7f8; --card: #ffffff; --text: #1f2328; --me: #dbeafe; --bot: #eef2f1; --border: #d0d7de; }
  @media (prefers-color-scheme: dark) { :root { --bg: #16181d; --card: #1f2229; --text: #e6e6e6; --me: #1e3a5f; --bot: #2a2f36; --border: #3a3f47; } }
  body { margin: 0; background: var(--bg); color: var(--text); font: 16px/1.5 system-ui, sans-serif; }
  main { max-width: 720px; margin: 0 auto; padding: 16px; display: flex; flex-direction: column; height: 100vh; box-sizing: border-box; }
  h1 { font-size: 20px; margin: 0 0 8px; }
  #log { flex: 1; overflow-y: auto; background: var(--card); border: 1px solid var(--border); border-radius: 12px; padding: 12px; }
  .msg { padding: 8px 12px; border-radius: 10px; margin: 6px 0; max-width: 85%; white-space: pre-wrap; }
  .user { background: var(--me); margin-left: auto; } .assistant { background: var(--bot); }
  form { display: flex; gap: 8px; margin-top: 12px; }
  input { flex: 1; padding: 10px; border-radius: 10px; border: 1px solid var(--border); background: var(--card); color: var(--text); font-size: 16px; }
  button { padding: 10px 16px; border-radius: 10px; border: 0; background: #2563eb; color: white; font-size: 16px; }
</style></head>
<body><main>
  <h1>TinyChat <small>(a 1M-parameter model you trained)</small></h1>
  <div id="log"></div>
  <form id="f"><input id="q" autocomplete="off" placeholder="Try: Who are you?" autofocus><button>Send</button></form>
</main>
<script>
const log = document.getElementById("log"), q = document.getElementById("q"), messages = [];
function add(role, text) {
  const d = document.createElement("div"); d.className = "msg " + role; d.textContent = text;
  log.appendChild(d); log.scrollTop = log.scrollHeight;
}
document.getElementById("f").onsubmit = async (e) => {
  e.preventDefault();
  const text = q.value.trim(); if (!text) return;
  q.value = ""; add("user", text); messages.push({role: "user", content: text});
  const r = await fetch("/chat", {method: "POST", headers: {"Content-Type": "application/json"}, body: JSON.stringify({messages})});
  const data = await r.json();
  add("assistant", data.reply); messages.push({role: "assistant", content: data.reply});
};
</script></body></html>"""


class Handler(BaseHTTPRequestHandler):
    def _send(self, code, body, content_type):
        data = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        if self.path == "/":
            self._send(200, PAGE, "text/html; charset=utf-8")
        else:
            self._send(404, "not found", "text/plain")

    def do_POST(self):
        if self.path != "/chat":
            return self._send(404, "not found", "text/plain")
        try:
            body = json.loads(self.rfile.read(int(self.headers.get("Content-Length", 0))))
            msgs = body["messages"]
            assert msgs and msgs[-1]["role"] == "user"
            history = [(m["role"], m["content"]) for m in msgs[:-1] if m["role"] in ("user", "assistant")]
        except (ValueError, KeyError, TypeError, AssertionError):
            return self._send(400, json.dumps({"error": "send {'messages': [..., {'role': 'user', 'content': '...'}]}"}), "application/json")
        with lock:
            answer, _ = reply(model, tok, history, str(msgs[-1]["content"])[:500])
        self._send(200, json.dumps({"reply": answer}), "application/json")


print(f"TinyChat web UI on http://{args.host}:{args.port}  (Ctrl+C to stop)")
try:
    ThreadingHTTPServer((args.host, args.port), Handler).serve_forever()
except KeyboardInterrupt:
    pass
