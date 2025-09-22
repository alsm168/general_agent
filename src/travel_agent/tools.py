"""Research Utilities and Tools.

This module provides search and content processing utilities for the research agent,
including web search capabilities and content summarization tools.
"""

from travel_agent.configuration import MapConfig
from langchain_mcp_adapters.client import MultiServerMCPClient

async def get_mcp_tools():
    """
    获取mcp工具列表
    """
    # Create a MapConfig instance with default values
    mcp_config = MapConfig()
    print('mcp_config=', mcp_config)
    mcp_tool_dict = {
        mcp_config.tool_name: {
            'url': mcp_config.url,
            'transport': mcp_config.transport,
        }
    }
    client = MultiServerMCPClient(mcp_tool_dict)
    return await client.get_tools()