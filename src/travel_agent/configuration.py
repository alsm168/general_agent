"""Define the configurable parameters for the file agent."""

from __future__ import annotations

from dataclasses import dataclass, field

from shared.configuration import BaseConfiguration
from typing import Annotated, TypedDict, Literal

@dataclass(kw_only=True)
class MapConfig:
    """
    用于MapAgent的配置类。
    此类定义了配置MapAgent所需的参数，包括采用的模型
    """
    tool_name: str = field(
        default='baidu-maps',
        metadata={
            "description": "用于MapAgent的工具名称."
        },
    )
    
    url: str = field(
        default='https://mcp.map.baidu.com/sse?ak=3aZKDTSvcLN50ocPNNA8f2ztg0eIX6Fy',
        metadata={
            "description": "用于MapAgent的URL."
        },
    )
    transport: Literal['sse', 'streamable_http'] = field(
        default='sse',
        metadata={
            "description": "用于MapAgent的传输协议. 可选值: sse, streamable_http."
        },
    )

    host: str = field(
        default='mcp.map.baidu.com',
        metadata={
            "description": f"用于MapAgent的主机名.(暂时未用)"
        },
    )

    port: int = field(
        default=443,
        metadata={
            "description": "用于MapAgent的端口号.(暂时未用)"
        },
    )

@dataclass(kw_only=True)
class MapConfiguration(BaseConfiguration):
    """
    用于WebSearchAgent的配置类。
    此类定义了配置WebSearchAgent所需的参数，包括采用的模型
    """

    query_model: Annotated[str, {"__template_metadata__": {"kind": "llm"}}] = field(
        default="openai/deepseek-chat", # deepseek-chat Qwen2.5-14B-Instruct
        metadata={
            "description": "处理和优化查询的模型. 以下列格式提供: provider/model-name."
        },
    )

    tool_call_iteration_limit: int = field(
        default=8,
        metadata={
            "description": "工具调用的最大迭代次数. 如果LLM在多次迭代中都没有触发工具调用, 则认为搜索失败."
        },
    )

    mcp_config: MapConfig = field(
        default_factory=MapConfig,
        metadata={
            "description": "用于MapAgent的配置."
        },
    )


