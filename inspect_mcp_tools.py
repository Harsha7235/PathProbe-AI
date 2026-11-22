import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

URL = "http://127.0.0.1:39400/mcp"

async def main():
    async with asyncio.timeout(30):
        async with streamable_http_client(URL) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.list_tools()

                print("TOTAL TOOLS:", len(result.tools))

                for tool in result.tools:
                    print("\n" + "=" * 55)
                    print("Name:", tool.name)
                    print("Description:", tool.description)
                    print("Input schema:", tool.input_schema)

asyncio.run(main())
