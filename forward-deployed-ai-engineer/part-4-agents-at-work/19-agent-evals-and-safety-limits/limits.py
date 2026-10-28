"""limits.py: hard safety limits that wrap any agent loop. Code enforces them; the model can't talk its way past.

  kill switch      a file called KILL_SWITCH (or AGENTS_KILL_SWITCH=1) stops every agent before its next step
  step cap         at most max_steps model calls per task
  cost cap         at most max_usd per task
  tool caps        e.g. issue_credit at most once per task
  money cap        a single credit above max_credit_gbp is blocked (the agent is told to escalate instead)
  loop detector    the same tool with the same arguments loop_threshold times in a row = stuck
"""
import json
import os
from dataclasses import dataclass, field
from pathlib import Path

KILL_SWITCH = Path(__file__).with_name("KILL_SWITCH")


class SafetyStop(Exception):
    """Stop the whole task now. .reason says which limit fired."""
    def __init__(self, reason: str):
        super().__init__(reason)
        self.reason = reason


def kill_switch_on() -> bool:
    return KILL_SWITCH.exists() or os.getenv("AGENTS_KILL_SWITCH") == "1"


@dataclass
class Limits:
    max_steps: int = 6
    max_usd: float = 0.25
    max_calls_per_tool: dict = field(default_factory=lambda: {"issue_credit": 1, "escalate_to_human": 1})
    max_credit_gbp: float = 10.0
    loop_threshold: int = 3


@dataclass
class Guard:
    limits: Limits = field(default_factory=Limits)
    steps: int = 0
    spent_usd: float = 0.0
    tool_counts: dict = field(default_factory=dict)
    recent: list = field(default_factory=list)

    def before_step(self):
        if kill_switch_on():
            raise SafetyStop("kill switch")
        if self.steps >= self.limits.max_steps:
            raise SafetyStop(f"step cap ({self.limits.max_steps})")
        if self.spent_usd >= self.limits.max_usd:
            raise SafetyStop(f"cost cap (${self.limits.max_usd})")
        self.steps += 1

    def charge(self, usd: float):
        self.spent_usd += usd

    def before_tool(self, name: str, args: dict) -> str | None:
        """Raise SafetyStop to end the task, return a message to BLOCK just this call, or None to allow it."""
        if kill_switch_on():
            raise SafetyStop("kill switch")
        signature = name + json.dumps(args, sort_keys=True)
        self.recent = (self.recent + [signature])[-self.limits.loop_threshold:]
        if len(self.recent) == self.limits.loop_threshold and len(set(self.recent)) == 1:
            raise SafetyStop(f"loop: {name} called {self.limits.loop_threshold} times with the same arguments")
        self.tool_counts[name] = self.tool_counts.get(name, 0) + 1
        cap = self.limits.max_calls_per_tool.get(name)
        if cap is not None and self.tool_counts[name] > cap:
            return f"BLOCKED: {name} may be used at most {cap} time(s) per task."
        if name == "issue_credit" and float(args.get("amount_gbp", 0)) > self.limits.max_credit_gbp:
            return (f"BLOCKED: credits above £{self.limits.max_credit_gbp:.2f} need a person. "
                    "Use escalate_to_human instead.")
        return None
