import asyncio
import json

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

URL = "http://127.0.0.1:39400/mcp"

TARGETS = {
    "pt_inspect_ports",
    "pt_verify_connectivity",
    "pt_read_packet_trace",
    "pt_query_topology",
}

async def main():
    async with asyncio.timeout(45):
        async with streamable_http_client(URL) as (read_stream, write_stream):
            async with ClientSession(read_stream, write_stream) as session:
                await session.initialize()
                result = await session.list_tools()

                for tool in result.tools:
                    if tool.name in TARGETS:
                        print("\n" + "=" * 65)
                        print("TOOL:", tool.name)
                        print("DESCRIPTION:", tool.description)
                        print("INPUT SCHEMA:")
                        print(json.dumps(tool.input_schema, indent=2))

asyncio.run(main())

