"""bad_tools.py: tool definitions that LOOK fine to a programmer but confuse a model. Compare with server.py.
Nothing runs these; tool_lint.py scores them so you can see what's wrong."""

BAD_TOOLS = [
    {   # one "god tool": the model has to invent URLs and JSON bodies, and can do ANYTHING
        "name": "api_call",
        "description": "Calls the API.",
        "input_schema": {"type": "object", "properties": {
            "method": {"type": "string"}, "path": {"type": "string"}, "body": {"type": "object"}}},
    },
    {   # vague name, camelCase, no description of the parameter, no idea when to use it
        "name": "getData",
        "description": "Gets data for an id.",
        "input_schema": {"type": "object", "properties": {"id": {"type": "string"}}, "required": ["id"]},
    },
    {   # fixed choices hidden in a free-text field; returns everything at once
        "name": "shipments",
        "description": "Returns all shipments for a customer as JSON, every field included.",
        "input_schema": {"type": "object", "properties": {
            "customer": {"type": "string", "description": "customer"},
            "status": {"type": "string", "description": "status of the shipment"}}},
    },
]
