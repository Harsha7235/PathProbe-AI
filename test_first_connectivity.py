import asyncio

from mcp import ClientSession
from mcp.client.streamable_http import streamable_http_client

URL = "http://127.0.0.1:39400/mcp"


async def main():
    async with asyncio.timeout(90):
        async with streamable_http_client(URL) as (
            read_stream,
            write_stream,
        ):
            async with ClientSession(
                read_stream,
                write_stream,
            ) as session:
                await session.initialize()

                result = await session.call_tool(
                    "pt_verify_connectivity",
                    {
                        "from_device": "Flour-1-L3",
                        "to_ip": "10.10.10.2",
                        "timeout_s": 60,
                    },
                )

                print("Tool error:", result.is_error)

                for item in result.content:
                    if hasattr(item, "text"):
                        print(item.text)
                    else:
                        print(item)


if __name__ == "__main__":
    asyncio.run(main())
