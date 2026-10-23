"""Tool calling with an open model: a small shop-assistant agent that runs fully on your computer.

The loop:  ask the model -> it may ask to use a tool -> we run the tool -> send the result back ->
           repeat until the model answers in plain text (or we hit MAX_STEPS).

Run:  python agent.py "Where is my order RB-2207, and what is 15% off 480 euros?"
      python agent.py            (chat; empty line to quit)
"""
import ast
import json
import operator
import os
import sys
from datetime import datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

import ollama

MODEL = os.environ.get("MODEL", "qwen2.5:3b")
MAX_STEPS = 6  # a safety limit: stop if the model keeps calling tools forever

# ---------- the tools: ordinary Python functions ----------
ORDERS = {  # a pretend order database
    "RB-2207": {"item": "City e-bike", "status": "in the workshop", "ready": "Friday"},
    "RB-1188": {"item": "Road bike", "status": "shipped", "ready": "arrives tomorrow"},
}


def get_order_status(order_number: str) -> str:
    order = ORDERS.get(order_number.strip().upper())
    return json.dumps(order) if order else f"No order called {order_number}."


# The only operations the calculator allows. (No ** power: 9**9**9 would freeze your computer.)
OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv,
       ast.USub: operator.neg}


def calculate(expression: str) -> str:
    """Safe calculator: only numbers and + - * / ( ). Never use eval() on text from an AI."""
    def walk(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in OPS:
            return OPS[type(node.op)](walk(node.left), walk(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in OPS:
            return OPS[type(node.op)](walk(node.operand))
        raise ValueError("only numbers and + - * / ( ) are allowed")
    try:
        return str(round(walk(ast.parse(expression, mode="eval").body), 4))
    except (ValueError, SyntaxError, ZeroDivisionError) as e:
        return f"Error: {e}"


def get_current_time(timezone: str = "Europe/London") -> str:
    try:
        return datetime.now(ZoneInfo(timezone)).strftime("%A %d %B %Y, %H:%M")
    except (ZoneInfoNotFoundError, ValueError):
        return f"Unknown time zone {timezone}. Use names like Europe/Paris or America/New_York."


FUNCTIONS = {"get_order_status": get_order_status, "calculate": calculate, "get_current_time": get_current_time}

# ---------- the menu we show the model: name, what it does, which arguments ----------
TOOLS = [
    {"type": "function", "function": {
        "name": "get_order_status",
        "description": "Look up a customer's order by its order number (like RB-1234).",
        "parameters": {"type": "object", "required": ["order_number"],
                       "properties": {"order_number": {"type": "string", "description": "e.g. RB-2207"}}}}},
    {"type": "function", "function": {
        "name": "calculate",
        "description": "Do arithmetic exactly. Use it for every calculation, e.g. '480 * 0.85'.",
        "parameters": {"type": "object", "required": ["expression"],
                       "properties": {"expression": {"type": "string", "description": "e.g. (2 + 3) * 4"}}}}},
    {"type": "function", "function": {
        "name": "get_current_time",
        "description": "Get the current date and time in a time zone.",
        "parameters": {"type": "object", "required": [],
                       "properties": {"timezone": {"type": "string", "description": "IANA name, e.g. Europe/Paris"}}}}},
]


def run_agent(messages):
    """Let the model think and use tools until it gives a final answer."""
    for _ in range(MAX_STEPS):
        response = ollama.chat(model=MODEL, messages=messages, tools=TOOLS, options={"temperature": 0})
        messages.append(response.message)  # remember what the model said (including its tool requests)

        if not response.message.tool_calls:  # no tool requested: this is the final answer
            return response.message.content

        for call in response.message.tool_calls:
            name, args = call.function.name, call.function.arguments  # arguments is already a dict
            if name in FUNCTIONS:
                try:
                    result = FUNCTIONS[name](**args)
                except TypeError as e:  # the model sent wrong argument names
                    result = f"Error: {e}"
            else:
                result = f"Error: there is no tool called {name}"
            print(f"  [tool] {name}({args}) -> {result}")
            messages.append({"role": "tool", "tool_name": name, "content": result})
    return "Sorry, I could not finish that in time."


def main():
    messages = [{"role": "system", "content":
                 "You are the assistant of Riverside Bikes. Use the tools for order lookups, maths and the time. "
                 "Never invent order details. Answer in 1-3 short sentences."}]
    try:
        if len(sys.argv) > 1:
            messages.append({"role": "user", "content": " ".join(sys.argv[1:])})
            print(run_agent(messages))
            return
        while question := input("\nYou: ").strip():
            messages.append({"role": "user", "content": question})
            print("Assistant:", run_agent(messages))
    except (EOFError, KeyboardInterrupt):  # Ctrl+D / Ctrl+C: leave quietly
        print()
    except ConnectionError:
        sys.exit("Can't reach Ollama. Open the Ollama app or run `ollama serve`.")
    except ollama.ResponseError as e:
        sys.exit(f"Ollama says: {e.error}  (try: ollama pull {MODEL})")


if __name__ == "__main__":
    main()
