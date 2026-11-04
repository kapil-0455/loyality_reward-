"""
MCP Client
Connects application agents to the Loyalty Reward MCP server.
"""

from fastmcp import Client

from backend.app.mcp.server import mcp


class LoyaltyMCPClient:
    def __init__(self):
        self.server = mcp

    async def call_tool(self, tool_name, parameters):
        """
        Calls an approved MCP tool and returns its result.
        """

        async with Client(self.server) as client:
            result = await client.call_tool(tool_name, arguments=parameters)

            return result
