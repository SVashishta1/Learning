# agent.py: a tiny "agent engine" used by every project in Part 6.
# An AGENT = an AI in a loop that can use TOOLS (your Python functions) until the job is done.
import json

import ai


def tool(function, description, inputs):
    """Describe a Python function so the AI knows when and how to use it.
    inputs: {"input_name": ("string" | "number" | "integer" | "boolean", "what it means")}"""
    return {"function": function, "definition": {
        "name": function.__name__, "description": description,
        "input_schema": {"type": "object",
                         "properties": {name: {"type": kind, "description": meaning} for name, (kind, meaning) in inputs.items()},
                         "required": list(inputs)}}}


WEB_SEARCH = {"type": "web_search_20260209", "name": "web_search", "max_uses": 3}   # Claude's built-in web search


def run_agent(task, tools=(), system="You are a helpful assistant.", name="Agent", web_search=False,
              needs_approval=(), max_steps=10, show=True, trace=None):
    """Give the agent a task. It thinks, uses tools, reads the results, and repeats until it has an answer."""
    by_name = {t["definition"]["name"]: t["function"] for t in tools}
    definitions = [t["definition"] for t in tools] + ([WEB_SEARCH] if web_search else [])
    messages = [{"role": "user", "content": task}]
    say = print if show else (lambda *a, **k: None)

    for step in range(max_steps):
        response = ai.send(messages=messages, system=system, max_tokens=4000, **({"tools": definitions} if definitions else {}))
        messages.append({"role": "assistant", "content": response.content})

        if response.stop_reason == "pause_turn":           # a long web search paused; let it continue
            continue
        if response.stop_reason != "tool_use":              # no tools wanted -> this is the final answer
            return "".join(b.text for b in response.content if b.type == "text")

        results = []
        for block in response.content:
            if block.type != "tool_use":
                continue
            if block.name in needs_approval and input(f"   ⚠️  {name} wants to run {block.name}({json.dumps(block.input)}). Allow? [y/N] ").lower() != "y":
                output = "The human said NO. Don't do this; explain or try something else."
            else:
                try:
                    output = str(by_name[block.name](**block.input))
                except Exception as error:                  # tell the AI what went wrong so it can fix it
                    output = f"Error: {error}"
            say(f"   🔧 {name} used {block.name}({json.dumps(block.input)}) → {output[:100]}")
            if trace is not None:                            # optional: collect tool uses (e.g. to show on a web page)
                trace.append(f"{block.name}({json.dumps(block.input)})")
            results.append({"type": "tool_result", "tool_use_id": block.id, "content": output})
        messages.append({"role": "user", "content": results})
    return "Stopped: too many steps."
