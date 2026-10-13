"""Let Claude use the MCP server's tools through the Anthropic SDK's MCP helpers + tool runner.
python claude_with_mcp.py "Add 3 flashcards about transformers, then quiz me on one."
"""
import asyncio
import sys

from anthropic import AsyncAnthropic
from anthropic.lib.tools.mcp import async_mcp_tool
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

import llm


async def main(request: str):
    client = AsyncAnthropic()
    async with stdio_client(StdioServerParameters(command=sys.executable, args=["server.py"])) as (read, write):
        async with ClientSession(read, write) as mcp_client:
            await mcp_client.initialize()
            tools = (await mcp_client.list_tools()).tools
            runner = client.beta.messages.tool_runner(       # the SDK runs the tool loop for us this time
                model=llm.MODEL, max_tokens=4000, **llm._extras(llm.MODEL),
                messages=[{"role": "user", "content": request}],
                tools=[async_mcp_tool(t, mcp_client) for t in tools])
            async for message in runner:
                for block in message.content:
                    if block.type == "text":
                        print(block.text)
                    elif block.type == "tool_use":
                        print(f"  🔧 {block.name}({block.input})")


asyncio.run(main(" ".join(sys.argv[1:]) or "Add two flashcards about LoRA under the topic 'fine-tuning', then show me my topics."))
