"""agent_core.py: a tiny multi-agent toolkit (~120 lines) built on the Claude API.

An Agent = name + system prompt + tools + the tool-calling loop (from project 7.4), plus:
  * Tool objects with Pydantic-validated inputs
  * optional HUMAN APPROVAL for risky tools
  * structured outputs (ask_structured)
  * token accounting and a readable trace
Frameworks like LangGraph, CrewAI or the OpenAI/Claude Agent SDKs package these same ideas.
"""
import json
from dataclasses import dataclass, field
from typing import Callable

from pydantic import BaseModel

import llm

COLORS = ["\033[96m", "\033[95m", "\033[93m", "\033[92m", "\033[94m", "\033[91m"]
RESET = "\033[0m"


@dataclass
class Tool:
    name: str
    description: str
    input_model: type[BaseModel]
    fn: Callable[..., str]
    needs_approval: bool = False          # risky actions pause for a human "yes"

    def definition(self) -> dict:
        schema = self.input_model.model_json_schema()
        return {"name": self.name, "description": self.description,
                "input_schema": {"type": "object", "properties": schema.get("properties", {}),
                                 "required": schema.get("required", []), **({"$defs": schema["$defs"]} if "$defs" in schema else {})}}


def cli_approver(agent_name: str, tool: str, args: dict) -> bool:
    answer = input(f"\n⚠️  {agent_name} wants to run {tool}({json.dumps(args)}). Allow? [y/N] ")
    return answer.strip().lower() in {"y", "yes"}


@dataclass
class Agent:
    name: str
    system: str
    tools: list[Tool] = field(default_factory=list)
    server_tools: list[dict] = field(default_factory=list)   # e.g. Claude's built-in web search
    client: object = None
    max_steps: int = 10
    effort: str = "medium"
    approver: Callable[[str, str, dict], bool] = cli_approver
    verbose: bool = True
    input_tokens: int = 0
    output_tokens: int = 0

    def __post_init__(self):
        self.client = self.client or llm.get_client()
        self.color = COLORS[hash(self.name) % len(COLORS)]

    def log(self, msg: str):
        if self.verbose:
            print(f"{self.color}[{self.name}]{RESET} {msg}")

    def _track(self, response):
        self.input_tokens += response.usage.input_tokens
        self.output_tokens += response.usage.output_tokens

    def _call_tool(self, block) -> dict:
        tool = next((t for t in self.tools if t.name == block.name), None)
        if tool is None:
            return {"type": "tool_result", "tool_use_id": block.id, "content": f"Unknown tool {block.name}", "is_error": True}
        try:
            args = tool.input_model(**block.input).model_dump()       # validate before running anything
            if tool.needs_approval and not self.approver(self.name, tool.name, args):
                self.log(f"🚫 {tool.name} declined by human")
                return {"type": "tool_result", "tool_use_id": block.id, "content": "The human reviewer DECLINED this action. Do not retry it; explain or choose another approach."}
            output = str(tool.fn(**args))
            self.log(f"🔧 {tool.name}({json.dumps(args)[:100]}) -> {output[:140]}")
            return {"type": "tool_result", "tool_use_id": block.id, "content": output}
        except Exception as e:
            self.log(f"❗ {tool.name} failed: {e}")
            return {"type": "tool_result", "tool_use_id": block.id, "content": f"{type(e).__name__}: {e}", "is_error": True}

    def run(self, task: str) -> str:
        """Give the agent a task; it loops (think -> tools -> think ...) until it has a final answer."""
        self.log(f"▶ {task[:120]}")
        messages = [{"role": "user", "content": task}]
        tool_defs = [t.definition() for t in self.tools] + self.server_tools
        for _ in range(self.max_steps):
            kwargs = {"tools": tool_defs} if tool_defs else {}
            response = llm.create(self.client, max_tokens=8000, system=self.system, messages=messages,
                                  output_config={"effort": self.effort}, **kwargs)
            self._track(response)
            messages.append({"role": "assistant", "content": response.content})
            if response.stop_reason == "pause_turn":
                continue
            if response.stop_reason != "tool_use":
                result = llm.text_of(response)
                self.log(f"✔ done ({len(result)} chars)")
                return result
            results = [self._call_tool(b) for b in response.content if b.type == "tool_use"]
            messages.append({"role": "user", "content": results})
        return f"[{self.name}] stopped after {self.max_steps} steps without finishing."

    def ask_structured(self, prompt: str, output_model: type[BaseModel]):
        """One call, typed answer. Great for routing, grading, planning and extraction."""
        response = llm.parse(self.client, max_tokens=8000, system=self.system, output_format=output_model,
                             messages=[{"role": "user", "content": prompt}], output_config={"effort": self.effort})
        self._track(response)
        self.log(f"📋 {output_model.__name__}: {str(response.parsed_output)[:140]}")
        return response.parsed_output


PRICES = {"claude-opus-5-5": (4.0, 20.0), "claude-sonnet-5-5": (2.0, 10.0), "claude-haiku-5-5": (0.10, 0.50)}


def cost_report(agents: list[Agent]) -> str:
    p_in, p_out = PRICES.get(llm.MODEL, (0, 0))
    lines, total = [], 0.0
    for a in agents:
        cost = (a.input_tokens * p_in + a.output_tokens * p_out) / 1e6
        total += cost
        lines.append(f"  {a.name:22s} {a.input_tokens:7d} in / {a.output_tokens:6d} out  ≈ ${cost:.4f}")
    return "\n".join(["Token usage per agent:"] + lines + [f"  {'TOTAL':22s} ≈ ${total:.4f}"])
