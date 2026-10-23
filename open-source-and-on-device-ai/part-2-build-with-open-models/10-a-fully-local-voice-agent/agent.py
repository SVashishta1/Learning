"""The agent's brain: a local LLM (Ollama) plus four tools that work without the internet.

Run on its own to TYPE to the agent (test the brain before adding ears and a mouth):
      python agent.py
voice_agent.py imports ask() and timer_alerts from this file.
"""
import json
import os
import queue
import sys
import threading
from datetime import datetime
from pathlib import Path

import httpx

OLLAMA = os.environ.get("OLLAMA_URL", "http://localhost:11434")
MODEL = os.environ.get("OLLAMA_MODEL", "llama3.2:3b")
NOTES = Path(__file__).with_name("notes.json")        # created the first time you add a note
timer_alerts = queue.Queue()                          # finished timers wait here until someone announces them

SYSTEM = ("You are a helpful voice assistant running on the user's own computer, with no internet. "
          "Your replies are spoken aloud: answer in 1-2 short sentences, with no lists, emojis or markdown. "
          "Use a tool when the user asks for the time, a timer, or notes. Never invent tool results.")
chat = [{"role": "system", "content": SYSTEM}]


# ---------- the tools: ordinary Python functions ----------
def get_time():
    return datetime.now().strftime("It is %H:%M on %A %d %B %Y.")


def timer_done(label):
    """Runs in the background when a timer rings."""
    print(f"\n⏰ Your {label} timer is done!")
    timer_alerts.put(f"Your {label} timer is done.")    # voice_agent.py also says it out loud


def set_timer(minutes, label="timer"):
    minutes = float(minutes)
    if not 0 < minutes <= 24 * 60:
        return "Error: a timer must be between a few seconds and 24 hours."
    alarm = threading.Timer(minutes * 60, timer_done, args=[label])   # call timer_done(label) later
    alarm.daemon = True                                # don't keep the program alive just for a timer
    alarm.start()
    return f"Timer '{label}' set for {minutes:g} minute{'' if minutes == 1 else 's'}."


def add_note(text):
    notes = json.loads(NOTES.read_text()) if NOTES.exists() else []
    notes.append({"text": text, "when": datetime.now().isoformat(timespec="minutes")})
    NOTES.write_text(json.dumps(notes, indent=2, ensure_ascii=False))
    return f"Saved note number {len(notes)}."


def read_notes():
    notes = json.loads(NOTES.read_text()) if NOTES.exists() else []
    if not notes:
        return "There are no notes yet."
    return " ".join(f"Note {i}: {n['text']}." for i, n in enumerate(notes, start=1))


TOOLS = {"get_time": get_time, "set_timer": set_timer, "add_note": add_note, "read_notes": read_notes}

# The "menu" we show the model: name, what it does, and which arguments it takes (as a JSON schema).
TOOL_SPECS = [
    {"type": "function", "function": {
        "name": "get_time", "description": "Get the current local time and date.",
        "parameters": {"type": "object", "properties": {}}}},
    {"type": "function", "function": {
        "name": "set_timer", "description": "Start a countdown timer.",
        "parameters": {"type": "object", "required": ["minutes"], "properties": {
            "minutes": {"type": "number", "description": "length in minutes, e.g. 0.5 for 30 seconds"},
            "label": {"type": "string", "description": "a short name such as 'tea' or 'pasta'"}}}}},
    {"type": "function", "function": {
        "name": "add_note", "description": "Save a short note for the user.",
        "parameters": {"type": "object", "required": ["text"], "properties": {
            "text": {"type": "string", "description": "the note, in the user's words"}}}}},
    {"type": "function", "function": {
        "name": "read_notes", "description": "Read back all saved notes.",
        "parameters": {"type": "object", "properties": {}}}},
]


def run_tool(name, arguments):
    """Run one tool the model asked for. Always return text, even when something goes wrong."""
    if name not in TOOLS:
        return f"Error: there is no tool called {name}."
    if isinstance(arguments, str):                      # some models send the arguments as a JSON string
        arguments = json.loads(arguments or "{}")
    try:
        return str(TOOLS[name](**arguments))
    except (TypeError, ValueError) as error:            # wrong or missing arguments
        return f"Error: {error}"


def recent_messages(keep=12):
    """The system message plus the last few messages, starting at a user message (never mid tool-call)."""
    recent = chat[1:][-keep:]
    while recent and recent[0]["role"] != "user":
        recent.pop(0)
    return chat[:1] + recent


def ask(text, max_rounds=5):
    """Send the user's words to the model; run tools until it gives a normal answer."""
    chat.append({"role": "user", "content": text})
    for _ in range(max_rounds):
        try:
            response = httpx.post(f"{OLLAMA}/api/chat", timeout=120, json={
                "model": MODEL, "messages": recent_messages(),
                "tools": TOOL_SPECS, "stream": False, "options": {"temperature": 0.2}})
        except httpx.ConnectError:
            sys.exit(f"Can't reach Ollama at {OLLAMA}. Open the Ollama app (or run 'ollama serve').")
        data = response.json()
        if "error" in data:
            sys.exit(f"Ollama says: {data['error']}. Did you run 'ollama pull {MODEL}'?")
        message = data["message"]
        chat.append(message)                            # remember what the model said (or asked for)
        calls = message.get("tool_calls") or []
        if not calls:
            return message.get("content", "").strip()   # a normal answer: we're done
        for call in calls:
            name, arguments = call["function"]["name"], call["function"].get("arguments") or {}
            result = run_tool(name, arguments)
            print(f"   🔧 {name}({json.dumps(arguments, ensure_ascii=False)}) → {result}")
            chat.append({"role": "tool", "tool_name": name, "content": result})
    return "Sorry, I got stuck using my tools. Please try again."


if __name__ == "__main__":
    print(f"⌨️  Typing mode with {MODEL}. Try: 'set a tea timer for 1 minute', 'note: buy oat milk', "
          "'what are my notes?', 'what time is it?'. Type 'bye' to stop.")
    while True:
        text = input("\n🧑 ").strip()
        if not text:
            continue
        print("🤖", ask(text))
        if text.lower() in {"bye", "goodbye", "quit", "exit"}:
            break
