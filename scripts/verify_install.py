"""Verify installed-wheel metadata and real stdio MCP discovery without Google calls.

Run with the clean environment's Python, outside editable source imports.
No tools are invoked and no credential is needed.
"""
import asyncio
import json
import sys
from importlib.metadata import version
from pathlib import Path

import anyio
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

import server


async def main():
    installed_path = Path(server.__file__).resolve()
    assert 'site-packages' in installed_path.parts, 'Use an installed wheel, not an editable checkout'
    params = StdioServerParameters(command=sys.executable, args=['-m', 'server'])
    with anyio.fail_after(20):
        async with stdio_client(params) as (read, write), ClientSession(read, write) as session:
            await session.initialize()
            tools = await session.list_tools()
            names = {tool.name for tool in tools.tools}
            assert {'find', 'get_note', 'create_list', 'update_list_item', 'trash_note'} <= names
    print(json.dumps({'installed_wheel': True, 'transport': 'stdio',
                      'tool_count': len(names), 'google_calls': 0,
                      'versions': {name: version(name) for name in ('keep-mcp', 'mcp', 'gkeepapi')}}))


if __name__ == '__main__':
    asyncio.run(main())
