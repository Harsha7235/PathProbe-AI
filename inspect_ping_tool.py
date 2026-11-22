import asyncio
from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

URL = "http://127.0.0.1:39400/mcp"

async def main():
    async with asyncio.timeout(45):
        async with streamable_http_client(URL) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.list_tools()

                for tool in result.tools:
                    if tool.name == "pt_verify_connectivity":
                        print("NAME:", tool.name)
                        print("DESCRIPTION:")
                        print(tool.description)
                        print("SCHEMA:")
                        print(tool.input_schema)

asyncio.run(main())
