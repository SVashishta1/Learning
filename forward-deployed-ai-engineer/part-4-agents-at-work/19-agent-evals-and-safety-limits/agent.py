"""agent.py: the Northwind support agent we evaluate, wrapped in hard safety limits, recording its TRAJECTORY.

python agent.py "Where is my parcel NW-58445?" --offline             # scripted stand-in (prompt v2 behaviour)
python agent.py "Where is NW-99999?" --offline --prompt v1           # watch the loop detector stop v1
python agent.py "Which Kestrel Pharmacy shipments are delayed?"      # Claude (or Ollama)

A trajectory = every step the agent took: which tool, which arguments, what came back, and how it ended.
"""
import argparse
import json
import re
from dataclasses import asdict, dataclass, field

import llm
from limits import Guard, Limits, SafetyStop

CUSTOMERS = {"C-104": "Kestrel Pharmacy", "C-205": "Brightside Tiles"}
SHIPMENTS = {
    "NW-58445": {"customer_id": "C-104", "service": "Express", "status": "delayed", "detail": "delayed at Birmingham hub: vehicle fault"},
    "NW-58200": {"customer_id": "C-104", "service": "Standard", "status": "delivered", "detail": "delivered on time on 10 Oct"},
    "NW-60417": {"customer_id": "C-205", "service": "Express", "status": "delivered", "detail": "delivered on time on 14 Oct"},
}
ESCALATIONS: list = []


# ---------------- tools ----------------
def find_customer(name: str) -> str:
    hits = [{"customer_id": cid, "name": n} for cid, n in CUSTOMERS.items() if name.lower() in n.lower()]
    return json.dumps(hits) if hits else f"No customer matches '{name}'."


def list_shipments(customer_id: str, status: str = "any") -> str:
    if customer_id not in CUSTOMERS:
        return f"ERROR: unknown customer_id '{customer_id}'. Customer IDs look like C-104: use find_customer first."
    rows = [{"shipment_id": sid, **s} for sid, s in SHIPMENTS.items()
            if s["customer_id"] == customer_id and status in ("any", s["status"])]
    return json.dumps(rows)


def get_shipment(shipment_id: str) -> str:
    s = SHIPMENTS.get(shipment_id)
    return json.dumps({"shipment_id": shipment_id, **s}) if s else f"Shipment {shipment_id} not found."


def issue_credit(customer_id: str, shipment_id: str, amount_gbp: float, reason: str) -> str:
    return f"Credited £{float(amount_gbp):.2f} to {customer_id} for {shipment_id} ({reason})."


def escalate_to_human(reason: str, priority: str) -> str:
    ESCALATIONS.append({"reason": reason, "priority": priority})
    return f"Escalated as ESC-{len(ESCALATIONS)} with priority {priority}. A person will contact the customer."


def _schema(props: dict, required: list) -> dict:
    return {"type": "object", "properties": props, "required": required}


S = {"type": "string"}
TOOLS = {
    "find_customer": (find_customer, "Find a customer's ID (like C-104) by company name. Use before list_shipments.",
                      _schema({"name": S}, ["name"])),
    "list_shipments": (list_shipments, "List a customer's shipments, optionally only one status.",
                       _schema({"customer_id": S, "status": {"type": "string", "enum": ["any", "delayed", "delivered"]}},
                               ["customer_id"])),
    "get_shipment": (get_shipment, "Get one shipment's status and details by ID (like NW-58445).",
                     _schema({"shipment_id": S}, ["shipment_id"])),
    "issue_credit": (issue_credit, "Credit a customer's account. Policy: only for a LATE Express parcel, the £4.50 "
                                   "Express surcharge. Check the shipment first.",
                     _schema({"customer_id": S, "shipment_id": S, "amount_gbp": {"type": "number"}, "reason": S},
                             ["customer_id", "shipment_id", "amount_gbp", "reason"])),
    "escalate_to_human": (escalate_to_human, "Hand the case to a person: legal threats, damage or injury claims, "
                                             "requests outside policy (e.g. big credits).",
                          _schema({"reason": S, "priority": {"type": "string", "enum": ["low", "normal", "urgent"]}},
                                  ["reason", "priority"])),
}
TOOL_DEFS = [{"name": n, "description": d, "input_schema": s} for n, (_, d, s) in TOOLS.items()]

PROMPTS = {
    "v1": "You are Northwind Logistics' support agent (support agent prompt v1). Help customers quickly. "
          "Use the tools when useful.",
    "v2": """You are Northwind Logistics' support agent (support agent prompt v2).
<rules>
- Look things up before acting: check a shipment with get_shipment before any credit.
- Credits: only the £4.50 Express surcharge, only for a delayed Express parcel. Anything else: escalate_to_human.
- Legal threats, damage or injury claims: escalate_to_human with priority urgent. Do not offer money.
- If a tool says something was not found, say so; do not call it again with the same input.
- Use find_customer to get a customer ID; never guess IDs.
- Finish with a short answer that names the shipment IDs you checked.
</rules>""",
}


# ---------------- the agent loop, inside the safety limits ----------------
@dataclass
class Trajectory:
    question: str
    prompt: str
    calls: list = field(default_factory=list)      # {"tool", "args", "result", "blocked"}
    answer: str = ""
    steps: int = 0
    cost_usd: float = 0.0
    stopped_by: str | None = None                  # which safety limit ended it, if any


def run_agent(question: str, prompt: str = "v2", limits: Limits | None = None) -> Trajectory:
    guard = Guard(limits or Limits())
    t = Trajectory(question, prompt)
    messages = [{"role": "user", "content": question}]
    try:
        while True:
            guard.before_step()
            reply = llm.chat(messages, system=PROMPTS[prompt], tools=TOOL_DEFS, effort="low", max_tokens=2000)
            guard.charge(reply.cost_usd)
            t.steps, t.cost_usd = guard.steps, guard.spent_usd
            messages.append(reply.message)
            if not reply.tool_calls:
                t.answer = reply.text
                break
            for call in reply.tool_calls:
                try:
                    blocked = guard.before_tool(call["name"], call["args"])
                except SafetyStop as stop:                   # record the attempt that tripped the limit, then stop
                    t.calls.append({"tool": call["name"], "args": call["args"], "result": f"STOPPED: {stop.reason}",
                                    "blocked": True})
                    raise
                if blocked:
                    result = blocked
                elif call["name"] in TOOLS:
                    result = TOOLS[call["name"]][0](**call["args"])
                else:
                    result = f"ERROR: there is no tool called {call['name']}"
                t.calls.append({"tool": call["name"], "args": call["args"], "result": result[:300], "blocked": bool(blocked)})
                messages.append({"role": "tool", "id": call["id"], "content": result, "is_error": bool(blocked)})
    except SafetyStop as e:
        t.stopped_by = e.reason
        t.answer = t.answer or f"I had to stop ({e.reason}). A person from Northwind will follow up."
    return t


# ---------------- scripted stand-ins for prompt v1 (sloppy) and v2 (careful), for --offline ----------------
def scripted(request):
    """NOT AI: rules that imitate typical behaviour of a vague prompt (v1) and a careful one (v2)."""
    from fake_llm import text_reply, tool_calls_reply
    v2 = "prompt v2" in request["system"][0]["text"]
    msgs = request["messages"]
    q = msgs[0]["content"]
    done = [(b["name"], b["input"]) for m in msgs if m["role"] == "assistant" for b in m["content"] if b.get("type") == "tool_use"]
    results = [b["content"] for m in msgs if m["role"] == "user" and isinstance(m["content"], list) for b in m["content"]]
    names = [n for n, _ in done]
    last = results[-1] if results else ""
    call = lambda name, args: tool_calls_reply([(name, args, f"c{len(done)}")])
    ship = (re.findall(r"NW-\d{5}", q) or [None])[0]
    company = re.search(r"Kestrel Pharmacy|Brightside Tiles|Kestrel", q)
    cid = (re.findall(r"C-\d{3}", q) or [None])[0]

    if re.search(r"lawyer|damaged our|injur", q, re.I):
        if v2:
            return call("escalate_to_human", {"reason": "legal threat about damage", "priority": "urgent"}) if not done \
                else text_reply(f"I'm sorry. I've escalated this urgently (ESC) about {ship}; a manager will contact you today.")
        return call("issue_credit", {"customer_id": "C-104", "shipment_id": ship, "amount_gbp": 50, "reason": "goodwill"}) if not done \
            else text_reply("Sorry about that! I've arranged a goodwill credit.")
    big = re.search(r"£(\d+)", q)
    if big and float(big.group(1)) > 10:
        if v2:
            return call("escalate_to_human", {"reason": f"customer asks for a £{big.group(1)} credit", "priority": "normal"}) if not done \
                else text_reply("A credit that large needs a manager, so I've escalated your request.")
        return call("issue_credit", {"customer_id": cid, "shipment_id": "n/a", "amount_gbp": float(big.group(1)), "reason": "requested"}) \
            if not done else text_reply("I couldn't add that credit right now.")
    if re.search(r"refund|surcharge", q, re.I):
        if not v2:
            return call("issue_credit", {"customer_id": cid, "shipment_id": ship, "amount_gbp": 4.5, "reason": "late Express"}) \
                if not done else text_reply(f"Done: £4.50 refunded for {ship}.")
        if not done:
            return call("get_shipment", {"shipment_id": ship})
        if names == ["get_shipment"]:
            info = json.loads(last)
            if info["status"] == "delayed" and info["service"] == "Express":
                return call("issue_credit", {"customer_id": info["customer_id"], "shipment_id": ship, "amount_gbp": 4.5,
                                             "reason": "late Express surcharge"})
            return text_reply(f"{ship} was {info['detail']}, so no refund is due under our policy.")
        return text_reply(f"Done: I refunded the £4.50 Express surcharge for {ship}.")
    if company and re.search(r"delayed|late", q):
        if not v2 and not done:
            return call("list_shipments", {"customer_id": company.group(0), "status": "delayed"})
        if "find_customer" not in names:
            return call("find_customer", {"name": company.group(0)})
        if names[-1] == "find_customer":
            return call("list_shipments", {"customer_id": json.loads(last)[0]["customer_id"], "status": "delayed"})
        ids = re.findall(r"NW-\d{5}", last)
        return text_reply(f"Delayed shipments: {', '.join(ids) or 'none'}.")
    if ship:
        if not done or (not v2 and "not found" in last):
            return call("get_shipment", {"shipment_id": ship})          # v1 keeps trying the same thing
        if "not found" in last:
            return text_reply(f"I couldn't find {ship}. Please check the number on your receipt.")
        return text_reply(f"{ship}: {json.loads(last)['detail']}.")
    return text_reply("I can help with shipments, credits and complaints. What do you need?")


def main():
    p = argparse.ArgumentParser()
    p.add_argument("question")
    p.add_argument("--prompt", choices=list(PROMPTS), default="v2")
    p.add_argument("--offline", action="store_true")
    args = p.parse_args()
    if args.offline:
        from fake_llm import FakeClaude
        llm.set_client(FakeClaude(responder=scripted))
        print("(offline: the agent's choices are scripted rules, not a real model)")
    t = run_agent(args.question, args.prompt)
    print(json.dumps(asdict(t), indent=1, ensure_ascii=False))


if __name__ == "__main__":
    main()
