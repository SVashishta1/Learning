"""Project 7.4: an AI agent = an LLM in a LOOP that can call tools.

    while True:
        ask the model (with tool definitions)
        if it wants tools -> run them, send results back, loop
        else -> it's done, print the answer

python agent.py "What's 17.5% of the price of 3 coffees at 4.20 each, and is it warmer in Rome or Oslo right now?"
"""
import json
import sys

import llm
from tools import run_tool, tool_definitions

SYSTEM = ("You are a helpful assistant with tools. Use the calculator for all arithmetic. "
          "Use web_search for recent facts. Think step by step, then give a short final answer.")


def run_agent(client, question: str, max_steps: int = 8, verbose: bool = True, web_search: bool = True) -> str:
    messages = [{"role": "user", "content": question}]
    tools = tool_definitions(include_web_search=web_search)
    for step in range(1, max_steps + 1):
        response = llm.create(client, max_tokens=4000, system=SYSTEM, tools=tools, messages=messages)
        messages.append({"role": "assistant", "content": response.content})   # keep EVERYTHING the model said
        if verbose:
            for block in response.content:
                if block.type == "server_tool_use":    # a search Anthropic already ran for us
                    print(f"  🌐 step {step}: {block.name}({json.dumps(block.input)})")

        if response.stop_reason == "pause_turn":       # a long server-side search paused; just continue
            continue
        if response.stop_reason != "tool_use":         # no more tools wanted -> final answer
            return llm.text_of(response)

        results = []
        for block in response.content:
            if block.type == "tool_use":
                output, is_error = run_tool(block.name, block.input)
                if verbose:
                    print(f"  🔧 step {step}: {block.name}({json.dumps(block.input)}) -> {output[:120]}")
                results.append({"type": "tool_result", "tool_use_id": block.id, "content": output, "is_error": is_error})
        messages.append({"role": "user", "content": results})       # ALL results in ONE message
    return "Stopped: reached the maximum number of steps."           # safety net against infinite loops


if __name__ == "__main__":
    client = llm.get_client()
    questions = sys.argv[1:] or [
        "What is (1234 * 5678) - 99, and what time is it in Tokyo?",
        "Is it warmer in Rome or Oslo right now? By how many degrees?",
        "Who won the most recent FIFA World Cup, and how many years ago was it?",
    ]
    for q in questions:
        print(f"\n❓ {q}")
        print(f"💬 {run_agent(client, q)}")
