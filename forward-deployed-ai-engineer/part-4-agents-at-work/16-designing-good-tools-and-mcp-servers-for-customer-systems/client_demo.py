"""client_demo.py: talk to the MCP server exactly like an AI app does (no AI involved).   python client_demo.py

It starts server.py as a child process (stdio transport), lists its tools, and calls some of them,
including two mistakes, so you can see the error messages a model would get back.
"""
import asyncio
import sys
from pathlib import Path

from mcp import Client, StdioServerParameters

SERVER = StdioServerParameters(command=sys.executable, args=[str(Path(__file__).with_name("server.py"))])


async def main():
    async with Client(SERVER) as client:
        print("TOOLS the server offers:")
        for t in (await client.list_tools()).tools:
            params = ", ".join(f"{p}{'' if p in t.input_schema.get('required', []) else '?'}"
                               for p in t.input_schema.get("properties", {}))
            kind = "read-only" if t.annotations and t.annotations.read_only_hint else "WRITES"
            print(f"  - {t.name}({params})  [{kind}]")

        calls = [("find_customers", {"query": "kestrel"}),
                 ("list_shipments", {"customer_id": "C-104", "status": "delayed"}),
                 ("get_shipment", {"shipment_id": "NW-58445", "detail": "full"}),
                 ("get_shipment", {"shipment_id": "NW-1234"}),                # wrong ID format
                 ("list_shipments", {"customer_id": "C-999"}),                # customer that doesn't exist
                 ("add_ticket_note", {"ticket_id": 9001, "note": "Reviewed late Express parcels.", "idempotency_key": "demo-note-9001"}),
                 ("add_ticket_note", {"ticket_id": 9001, "note": "Reviewed late Express parcels.", "idempotency_key": "demo-note-9001"})]
        for name, args in calls:
            result = await client.call_tool(name, args)
            text = result.content[0].text.replace("\n", "\n      ")
            print(f"\n{'❌' if result.is_error else '→'} {name}({args})\n      {text[:400]}")

        resource = await client.read_resource("northwind://guide")
        print(f"\nRESOURCE northwind://guide -> {resource.contents[0].text[:90]}...")
        prompt = await client.get_prompt("investigate_late_shipments", {"company": "Kestrel Pharmacy"})
        print(f"PROMPT investigate_late_shipments -> {prompt.messages[0].content.text[:90]}...")


asyncio.run(main())
