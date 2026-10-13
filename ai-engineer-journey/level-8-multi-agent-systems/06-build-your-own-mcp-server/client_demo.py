"""Talk to the MCP server directly (no AI involved) to see exactly what an AI app sees.  python client_demo.py"""
import asyncio
import sys

from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client


async def main():
    server = StdioServerParameters(command=sys.executable, args=["server.py"])
    async with stdio_client(server) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            print("TOOLS the server offers:")
            for t in tools.tools:
                print(f"  - {t.name}: {t.description}")
            r = await session.call_tool("add_note", {"topic": "RAG", "question": "What does the R in RAG stand for?", "answer": "Retrieval"})
            print("\nadd_note ->", r.content[0].text)
            r = await session.call_tool("quiz_me", {"topic": "RAG"})
            print("quiz_me  ->", r.content[0].text)
            res = await session.read_resource("notes://topics")
            print("resource notes://topics ->", res.contents[0].text)


asyncio.run(main())
