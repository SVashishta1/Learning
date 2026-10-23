# value_calculator.py: is this AI project worth it? Turn assumptions into cost, value and break-even.
#
#   python value_calculator.py northwind_assumptions.json
#   python value_calculator.py northwind_assumptions.json --model claude-haiku-5-5
#   python value_calculator.py northwind_assumptions.json --set acceptance_rate=0.35
#
# Every assumption in the JSON file has a "value" and a "source". If you can't name the source,
# it's a guess: say so in the design doc and plan how to measure it.
import argparse
import json
import sys
from pathlib import Path

# Price in US dollars per 1 million tokens (input, output), as of October 2026.
# Prices change: check https://platform.claude.com/docs/en/about-claude/pricing
PRICES = {
    "claude-opus-5-5": (4.00, 20.00),
    "claude-sonnet-5-5": (2.00, 10.00),
    "claude-haiku-5-5": (0.10, 0.50),
    "local-open-model": (0.00, 0.00),       # no per-token price; you pay for the hardware in infra_cost_per_month
}
WEEKS_PER_MONTH = 52 / 12                    # about 4.33


def load(path):
    """Read the JSON file and keep only the values: {"emails_per_week": 9000, ...}."""
    raw = json.loads(Path(path).read_text(encoding="utf-8"))
    return {name: item["value"] for name, item in raw.items()}


def apply_overrides(values, overrides):
    """--set name=number lets you try 'what if' without editing the file."""
    for text in overrides or []:
        name, _, number = text.partition("=")
        if name not in values:
            raise KeyError(f"Unknown assumption {name!r}. Known: {', '.join(values)}")
        values[name] = type(values[name])(number) if not isinstance(values[name], str) else number
    return values


def calculate(v):
    """All the maths in one place. Returns a dictionary of results (monthly unless the name says otherwise)."""
    if v["model"] not in PRICES:
        raise KeyError(f"No price for model {v['model']!r}. Add it to PRICES.")
    price_in, price_out = PRICES[v["model"]]
    tickets = v["emails_per_week"] * WEEKS_PER_MONTH * v["share_in_scope"]          # AI-eligible tickets per month
    cost_per_ticket = (v["input_tokens_per_ticket"] * price_in
                       + v["output_tokens_per_ticket"] * price_out) / 1_000_000
    llm_cost = tickets * cost_per_ticket
    # Time is saved only when the agent accepts the draft. Rejected drafts save nothing (we assume no extra cost).
    minutes_saved = tickets * v["acceptance_rate"] * (v["minutes_today"] - v["minutes_with_ai"])
    hours_saved = minutes_saved / 60
    value = hours_saved * v["agent_cost_per_hour"]
    net = value - llm_cost - v["infra_cost_per_month"]
    break_even = v["build_cost"] / net if net > 0 else None                         # months to pay back the build
    return {"tickets": tickets, "cost_per_ticket": cost_per_ticket, "llm_cost": llm_cost,
            "hours_saved": hours_saved, "value": value, "net": net, "break_even_months": break_even}


def report(v, r):
    lines = [f"Model: {v['model']}",
             f"AI-eligible tickets per month:  {r['tickets']:>12,.0f}",
             f"LLM cost per ticket:            {r['cost_per_ticket']:>12.4f} USD",
             f"LLM cost per month:             {r['llm_cost']:>12,.0f} USD",
             f"Infrastructure per month:       {v['infra_cost_per_month']:>12,.0f} USD",
             f"Agent hours saved per month:    {r['hours_saved']:>12,.0f} h",
             f"Value of time saved per month:  {r['value']:>12,.0f} USD",
             f"Net value per month:            {r['net']:>12,.0f} USD"]
    if r["break_even_months"] is None:
        lines.append("Break-even: never (the project costs more each month than it saves)")
    else:
        lines.append(f"Break-even on the build cost:   {r['break_even_months']:>12.1f} months")
    return "\n".join(lines)


def main():
    parser = argparse.ArgumentParser(description="Estimate the monthly cost and value of an AI project.")
    parser.add_argument("assumptions", help="JSON file of assumptions, each with a value and a source")
    parser.add_argument("--model", help="try another model, e.g. claude-haiku-5-5")
    parser.add_argument("--set", action="append", metavar="NAME=NUMBER",
                        help="change one assumption, e.g. --set acceptance_rate=0.35 (repeatable)")
    args = parser.parse_args()
    try:
        values = apply_overrides(load(args.assumptions), args.set)
        if args.model:
            values["model"] = args.model
        print(report(values, calculate(values)))
    except FileNotFoundError:
        sys.exit(f"Can't find {args.assumptions}.")
    except (KeyError, ValueError) as problem:
        sys.exit(f"Problem: {problem.args[0]}")


if __name__ == "__main__":
    main()
