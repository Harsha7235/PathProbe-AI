import asyncio
import json
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

URL = "http://127.0.0.1:39400/mcp"

async def main():
    async with asyncio.timeout(45):
        async with streamable_http_client(URL) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()

                result = await session.call_tool("pt_export_topology", {})

                print("ERROR:", result.is_error)
                print("CONTENT BLOCKS:", len(result.content))

                for i, block in enumerate(result.content):
                    print(f"\n--- BLOCK {i} ---")
                    if hasattr(block, "text"):
                        text = block.text
                        print("TYPE: text")
                        print(text[:12000])
                    else:
                        print(type(block).__name__, str(block)[:2000])

asyncio.run(main())
