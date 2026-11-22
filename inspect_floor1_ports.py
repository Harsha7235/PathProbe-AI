import asyncio

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

URL = "http://127.0.0.1:39400/mcp"


async def main():
    async with asyncio.timeout(60):
        async with streamable_http_client(URL) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()

                result = await session.call_tool(
                    "pt_inspect_ports",
                    {
                        "device": "Floor 1",
                        "only_linked": True,
                    },
                )

                print("Tool error:", result.is_error)

                for item in result.content:
                    if hasattr(item, "text"):
                        print(item.text)


asyncio.run(main())
