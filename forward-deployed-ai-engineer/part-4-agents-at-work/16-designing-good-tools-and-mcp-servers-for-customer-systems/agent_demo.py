"""agent_demo.py: a model uses the MCP server's tools to answer a question (the full loop, written out).

python agent_demo.py "Which Kestrel Pharmacy shipments are delayed, and why?" --offline   # free stand-in
python agent_demo.py "Which Kestrel Pharmacy shipments are delayed, and why?"             # Claude (or Ollama)
"""
import argparse
import asyncio
import re
import sys
from pathlib import Path

from mcp import Client, StdioServerParameters

import llm

SERVER = StdioServerParameters(command=sys.executable, args=[str(Path(__file__).with_name("server.py"))])
SYSTEM = ("You are Northwind Logistics' operations assistant. Use the tools to look things up; never guess IDs. "
          "Answer briefly and mention the shipment IDs you checked.")


def to_model_tools(mcp_tools) -> list[dict]:
    """MCP tool list -> the tool format the model API expects. The schemas are passed through unchanged."""
    return [{"name": t.name, "description": t.description, "input_schema": t.input_schema} for t in mcp_tools]


async def run(question: str, max_steps: int = 8) -> str:
    async with Client(SERVER) as client:
        tools = to_model_tools((await client.list_tools()).tools)
        messages = [{"role": "user", "content": question}]
        for step in range(1, max_steps + 1):
            reply = llm.chat(messages, system=SYSTEM, tools=tools, effort="low", max_tokens=2000)
            messages.append(reply.message)
            if not reply.tool_calls:
                return reply.text
            for call in reply.tool_calls:
                result = await client.call_tool(call["name"], call["args"])      # the MCP server does the work
                text = "\n".join(c.text for c in result.content if c.type == "text")
                print(f"  step {step}: {'❌' if result.is_error else '🔧'} {call['name']}({call['args']}) -> "
                      f"{text.splitlines()[0][:80]}")
                messages.append({"role": "tool", "id": call["id"], "content": text, "is_error": result.is_error})
        return f"Stopped after {max_steps} steps without a final answer."


def offline_responder(request):
    """A scripted stand-in (NOT an AI): find the customer -> list delayed shipments -> read each one -> summarise.
    It reads the REAL tool results to pick the next IDs, so the tool calls and data are genuine."""
    from fake_llm import text_reply, tool_calls_reply
    turns = sum(m["role"] == "assistant" for m in request["messages"])
    last = request["messages"][-1]["content"]
    results = " ".join(str(b.get("content", "")) for b in last) if isinstance(last, list) else ""
    if turns == 0:
        names = re.findall(r"\b[A-Z][a-z]{2,}\b", last)          # capitalised words = probably the company
        name = names[1] if last.startswith(names[0]) and len(names) > 1 else names[0]
        return tool_calls_reply([("find_customers", {"query": name.lower()}, "c1")])
    if turns == 1:
        customer = re.search(r"C-\d{3}", results).group(0)
        return tool_calls_reply([("list_shipments", {"customer_id": customer, "status": "delayed"}, "c2")])
    if turns == 2:
        ids = re.findall(r"NW-\d{5}", results)
        if not ids:
            return text_reply(results.strip() or "I found no delayed shipments.")
        return tool_calls_reply([("get_shipment", {"shipment_id": sid, "detail": "full"}, f"c3-{i}") for i, sid in enumerate(ids)])
    lines = [line.strip() for line in results.splitlines() if "delayed at" in line]
    ids = re.findall(r"NW-\d{5}", results)
    return text_reply(f"{len(set(ids))} delayed shipment(s): " + "; ".join(f"{i}: {l.split('  ', 1)[-1]}" for i, l in zip(ids, lines)))


def main():
    p = argparse.ArgumentParser()
    p.add_argument("question", nargs="?", default="Which Kestrel Pharmacy shipments are delayed, and why?")
    p.add_argument("--offline", action="store_true")
    args = p.parse_args()
    if args.offline:
        from fake_llm import FakeClaude
        llm.set_client(FakeClaude(responder=offline_responder))
        print("(offline: a scripted stand-in chooses the tools; the MCP server and its data are real)")
    print(f"QUESTION: {args.question}")
    print(f"ANSWER: {asyncio.run(run(args.question))}")


if __name__ == "__main__":
    main()
