"""The agent's tools. Each tool = a Python function + a Pydantic model describing its inputs.
The model's description and field descriptions are what Claude reads to decide WHEN and HOW to use a tool."""
import ast
import operator
from datetime import datetime
from zoneinfo import ZoneInfo

import httpx
from pydantic import BaseModel, Field


class CalculatorInput(BaseModel):
    """Evaluate an arithmetic expression exactly. Use this for ANY maths instead of doing it in your head."""
    expression: str = Field(description="e.g. '(12.5 * 4) / 3 + 2 ** 10'. Supports + - * / // % ** and parentheses.")


class WeatherInput(BaseModel):
    """Get the current temperature and wind for a city."""
    city: str = Field(description="City name, e.g. 'Tokyo'")


class TimeInput(BaseModel):
    """Get the current local date and time in a timezone."""
    timezone: str = Field(description="IANA timezone, e.g. 'Asia/Kolkata', 'America/New_York', 'Europe/London'")


_OPS = {ast.Add: operator.add, ast.Sub: operator.sub, ast.Mult: operator.mul, ast.Div: operator.truediv,
        ast.FloorDiv: operator.floordiv, ast.Mod: operator.mod, ast.Pow: operator.pow, ast.USub: operator.neg}


def calculator(expression: str) -> str:
    """SAFE evaluation: we walk the syntax tree and only allow numbers and maths operators.
    Never use eval() on model output: it could run any Python code!"""
    def ev(node):
        if isinstance(node, ast.Constant) and isinstance(node.value, (int, float)):
            return node.value
        if isinstance(node, ast.BinOp) and type(node.op) in _OPS:
            if isinstance(node.op, ast.Pow) and abs(ev(node.right)) > 1000:
                raise ValueError("exponent too large")
            return _OPS[type(node.op)](ev(node.left), ev(node.right))
        if isinstance(node, ast.UnaryOp) and type(node.op) in _OPS:
            return _OPS[type(node.op)](ev(node.operand))
        raise ValueError(f"not allowed: {ast.dump(node)[:40]}")
    return str(ev(ast.parse(expression, mode="eval").body))


def get_weather(city: str) -> str:
    geo = httpx.get("https://geocoding-api.open-meteo.com/v1/search", params={"name": city, "count": 1}, timeout=10).json()
    if not geo.get("results"):
        return f"No city called {city} found."
    p = geo["results"][0]
    cur = httpx.get("https://api.open-meteo.com/v1/forecast", timeout=10, params={
        "latitude": p["latitude"], "longitude": p["longitude"], "current": "temperature_2m,wind_speed_10m"}).json()["current"]
    return f"{p['name']}, {p.get('country', '')}: {cur['temperature_2m']}°C, wind {cur['wind_speed_10m']} km/h"


def get_time(timezone: str) -> str:
    return datetime.now(ZoneInfo(timezone)).strftime("%A %d %B %Y, %H:%M (%Z)")


# name -> (function, input model)
REGISTRY = {"calculator": (calculator, CalculatorInput), "get_weather": (get_weather, WeatherInput),
            "get_time": (get_time, TimeInput)}


def tool_definitions(include_web_search=True) -> list[dict]:
    defs = []
    for name, (_, model) in REGISTRY.items():
        schema = model.model_json_schema()
        defs.append({"name": name, "description": model.__doc__.strip(),
                     "input_schema": {"type": "object", "properties": schema["properties"], "required": schema.get("required", [])}})
    if include_web_search:
        # A SERVER tool: Anthropic runs the search for us. No code or extra API key needed on our side.
        defs.append({"type": "web_search_20260209", "name": "web_search", "max_uses": 3})
    return defs


def run_tool(name: str, args: dict) -> tuple[str, bool]:
    """Returns (result_text, is_error). Errors go back to the model so it can fix its call."""
    if name not in REGISTRY:
        return f"Unknown tool {name}", True
    fn, model = REGISTRY[name]
    try:
        valid = model(**args)                    # validate the model's arguments before running anything
        return fn(**valid.model_dump()), False
    except Exception as e:
        return f"{type(e).__name__}: {e}", True
