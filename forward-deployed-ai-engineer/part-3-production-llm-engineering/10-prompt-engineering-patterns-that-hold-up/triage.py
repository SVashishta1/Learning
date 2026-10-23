"""triage.py: Northwind support-ticket triage with a prompt that holds up in production.

python triage.py --show-prompt           # print the exact request we would send (free, no API call)
python triage.py --offline               # run the 8 sample tickets through an offline stand-in model (free)
python triage.py                         # run the 8 sample tickets through Claude with prompt v2
python triage.py --version 1             # same with the old prompt v1, to compare
python triage.py "Parcel NW-12345 arrived crushed"    # triage one ticket of your own
"""
import json
import re
import sys
from pathlib import Path
from typing import Literal

from pydantic import BaseModel, Field, ValidationError

import llm
import prompt_kit


# ---------- 1. The shape we want back (structured output) ----------
class Triage(BaseModel):
    category: Literal["late_delivery", "damaged_goods", "lost_shipment", "billing", "address_change", "other"]
    priority: Literal["low", "normal", "high", "urgent"]
    shipment_id: str | None = Field(description="Shipment ID like NW-12345 copied from the ticket, or null")
    sentiment: Literal["angry", "unhappy", "neutral", "positive"]
    summary: str = Field(description="One plain-English sentence, at most 25 words")
    needs_human: bool = Field(description="True for legal threats, injuries, safety issues or when unsure")


# ---------- 2. Build the request from a versioned prompt file ----------
def build_request(ticket: str, version: int | None = None) -> dict:
    prompt = prompt_kit.load("triage", version)
    return {"system": prompt.system, "user": prompt.render_user(ticket=ticket),
            "version": prompt.version, "fingerprint": prompt.fingerprint}


# ---------- 3. Never trust, always verify: checks AFTER the model answers ----------
SHIPMENT_ID = re.compile(r"\bNW-\d{5}\b")


def verify(result: Triage, ticket: str) -> tuple[Triage, list[str]]:
    warnings = []
    if result.shipment_id and result.shipment_id not in SHIPMENT_ID.findall(ticket):
        warnings.append(f"model returned shipment_id {result.shipment_id!r}, which is not in the ticket: removed")
        result = result.model_copy(update={"shipment_id": None, "needs_human": True})
    if len(result.summary.split()) > 40:
        warnings.append("summary is longer than 40 words")
    return result, warnings


def parse_loose(text: str) -> Triage:
    """For v1 (no schema): dig JSON out of free text. This is the fragile thing structured outputs replace."""
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if not match:
        raise ValueError("no JSON found in the reply")
    return Triage.model_validate_json(match.group(0))


def triage(ticket: str, version: int | None = None) -> dict:
    req = build_request(ticket, version)
    record = {"version": req["version"], "fingerprint": req["fingerprint"]}   # log which prompt made this answer
    try:
        if req["version"] >= 2:
            reply = llm.chat(req["user"], system=req["system"], schema=Triage, max_tokens=1000, effort="low")
            result = reply.parsed
        else:
            reply = llm.chat(req["user"], system=req["system"], max_tokens=1000, effort="low")
            result = parse_loose(reply.text)
    except (ValueError, ValidationError) as e:
        return record | {"ok": False, "error": str(e).splitlines()[0][:90]}
    result, warnings = verify(result, ticket)
    return record | {"ok": True, "triage": result.model_dump(), "warnings": warnings,
                     "tokens": [reply.input_tokens, reply.output_tokens]}


# ---------- 4. An offline stand-in model (keyword rules), so you can run everything without a key ----------
def offline_responder(request: dict):
    """Pretends to be Claude. NOT an AI: simple keyword rules. With a schema it returns clean JSON;
    without one (prompt v1) it imitates a typical v1 failure: chatty text and labels in its own words."""
    from fake_llm import json_reply, text_reply
    text = request["messages"][-1]["content"].lower()
    t = text
    if re.search(r"charged|invoice|refund", t):
        category = "billing"
    elif re.search(r"crushed|cracked|broken|torn|damaged", t):
        category = "damaged_goods"
    elif "never arrived" in t and re.search(r"\b([5-9]|\d\d) days", t):
        category = "lost_shipment"
    elif re.search(r"late|promised|hasn't moved|stuck", t):
        category = "late_delivery"
    elif re.search(r"address|new unit", t):
        category = "address_change"
    else:
        category = "other"
    if re.search(r"lawyer|insulin|chilled|cold chain|medicine|injur", t):
        priority = "urgent"
    elif re.search(r"again|third time|every week", t):
        priority = "high"
    elif "?" in t and category in ("address_change", "other"):
        priority = "low"
    else:
        priority = "normal"
    ids = SHIPMENT_ID.findall(request["messages"][-1]["content"])
    answer = {"category": category, "priority": priority, "shipment_id": ids[0] if ids else None,
              "sentiment": "angry" if "!" in t or "now" in t else "unhappy" if category != "other" else "neutral",
              "summary": "Customer reports a " + category.replace("_", " ") + " issue.",
              "needs_human": priority == "urgent"}
    if "format" in request.get("output_config", {}):
        return json_reply(answer)
    loose = {"Category": category.replace("_", " ").title(), "Priority": priority.title(), "ShipmentID": answer["shipment_id"]}
    return text_reply("Sure! Here is the classification for this ticket:\n```json\n" + json.dumps(loose, indent=1) + "\n```")


# ---------- 5. Command line ----------
def run_samples(version):
    cases = [json.loads(line) for line in Path(__file__).with_name("tickets.jsonl").open(encoding="utf-8")]
    correct = 0
    print(f"Prompt triage v{prompt_kit.load('triage', version).version} on {len(cases)} sample tickets")
    print(f"{'ticket':7s} {'expected':24s} {'got':40s} ok")
    for case in cases:
        out = triage(case["ticket"], version)
        exp = case["expected"]
        if out["ok"]:
            got = out["triage"]
            hit = all(got[k] == exp[k] for k in ("category", "priority", "shipment_id"))
            label = f"{got['category']}/{got['priority']}"
        else:
            hit, label = False, "INVALID: " + out["error"][:30]
        correct += hit
        print(f"{case['id']:7s} {exp['category'] + '/' + exp['priority']:24s} {label:40s} {'✅' if hit else '❌'}")
        for w in out.get("warnings", []):
            print(f"        ⚠️  {w}")
    print(f"Score: {correct}/{len(cases)} exactly right (category + priority + shipment_id)")


def main(argv):
    version = int(argv[argv.index("--version") + 1]) if "--version" in argv else None
    if "--offline" in argv:
        from fake_llm import FakeClaude
        llm.set_client(FakeClaude(responder=offline_responder))
        print("(offline: answers come from keyword rules in offline_responder(), not from a real model)\n")
    words = [a for i, a in enumerate(argv) if not a.startswith("--") and (i == 0 or argv[i - 1] != "--version")]
    if "--show-prompt" in argv:
        req = build_request(words[0] if words else "Parcel NW-12345 is late <b>again</b>!", version)
        print(f"PROMPT triage v{req['version']} (fingerprint {req['fingerprint']})\n")
        print("----- SYSTEM -----\n" + req["system"] + "\n\n----- USER -----\n" + req["user"])
        print("\n----- OUTPUT SHAPE (part of the JSON schema sent as output_config.format) -----")
        for name, field in Triage.model_json_schema()["properties"].items():
            print(f"{name:12s} {field.get('enum') or field.get('type') or 'string or null'}")
    elif words:
        print(json.dumps(triage(" ".join(words), version), indent=2))
    else:
        run_samples(version)


if __name__ == "__main__":
    main(sys.argv[1:])
