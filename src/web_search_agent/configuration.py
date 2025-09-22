"""Define the configurable parameters for the file agent."""

from __future__ import annotations

from dataclasses import dataclass, field

from shared.configuration import BaseConfiguration

from typing import Annotated


@dataclass(kw_only=True)
class WebSearchConfiguration(BaseConfiguration):
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
        default=3,
        metadata={
            "description": "工具调用的最大迭代次数. 如果LLM在多次迭代中都没有触发工具调用, 则认为搜索失败."
        },
    )
