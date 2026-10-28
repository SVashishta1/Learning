"""tool_lint.py: check tool definitions against a checklist of what makes tools easy for a model to use well.

python tool_lint.py     # scores the bad examples in bad_tools.py and the real tools in server.py
"""
import asyncio
import re

VERBS = ("get", "list", "find", "search", "create", "add", "update", "cancel", "send", "book", "check", "close")
GOD_PARAMS = {"method", "path", "url", "body", "payload", "sql", "query_json", "data", "command"}
CHOICE_WORDS = ("status", "type", "mode", "format", "detail", "kind", "level")


def lint(tool: dict) -> list[str]:
    """Return a list of problems. Each one is a real reason models pick the wrong tool or fill it in wrongly."""
    problems = []
    name, desc = tool["name"], tool.get("description") or ""
    props = tool.get("input_schema", {}).get("properties", {})
    if not re.fullmatch(r"[a-z]+(_[a-z]+)+", name):
        problems.append("name should be snake_case verb_noun, like get_shipment")
    elif not name.startswith(VERBS):
        problems.append(f"name should start with a verb ({', '.join(VERBS[:5])}...)")
    if len(desc) < 60:
        problems.append("description too short: say what it does, when to use it, and what it returns")
    if not re.search(r"\buse\b|\bwhen\b", desc, re.I):
        problems.append("description should say WHEN to use it (or when to use another tool instead)")
    for pname, schema in props.items():
        if pname in GOD_PARAMS:
            problems.append(f"'{pname}' is a do-anything parameter: offer specific tools instead")
        has_rule = any(k in schema for k in ("enum", "pattern", "minimum", "maximum", "minLength"))
        if len(schema.get("description", "")) < 15 and not has_rule:
            problems.append(f"parameter '{pname}' needs a description with an example or format")
        if any(w in pname for w in CHOICE_WORDS) and "enum" not in schema:
            problems.append(f"parameter '{pname}' looks like a fixed choice: list the allowed values (enum)")
    if props and "required" not in tool.get("input_schema", {}):
        problems.append("schema has no 'required' list: the model can't tell what it must fill in")
    annotations = tool.get("annotations")
    if annotations is not None and not annotations.get("read_only_hint") and annotations.get("idempotent_hint") is None:
        problems.append("write tool should declare whether retrying is safe (idempotent_hint)")
    return problems


async def server_tools() -> list[dict]:
    """Ask our MCP server for its tools, exactly as an AI app would see them."""
    from mcp import Client
    import server
    async with Client(server.mcp) as client:
        tools = (await client.list_tools()).tools
    return [{"name": t.name, "description": t.description, "input_schema": t.input_schema,
             "annotations": t.annotations.model_dump() if t.annotations else {}} for t in tools]


def report(title: str, tools: list[dict]):
    print(f"== {title} ==")
    for tool in tools:
        problems = lint(tool)
        print(f"{'✅' if not problems else '❌'} {tool['name']:20s} {max(0, 10 - 2 * len(problems))}/10")
        for p in problems:
            print(f"     - {p}")
    if len(tools) > 20:
        print("   ⚠️  more than 20 tools: models choose worse with long tool lists; split by task")


if __name__ == "__main__":
    from bad_tools import BAD_TOOLS
    report("bad_tools.py", BAD_TOOLS)
    print()
    report("server.py (MCP)", asyncio.run(server_tools()))
