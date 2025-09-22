"""Define the configurable parameters for the file agent."""

from __future__ import annotations

from dataclasses import dataclass, field

from shared.configuration import BaseConfiguration

from typing import Annotated


@dataclass(kw_only=True)
class FileAgentConfiguration(BaseConfiguration):
    """
    用于FileAgent的配置类。
    此类定义了配置FileAgent所需的参数，包括采用的模型、存储的根目录
    """

    root_dir: str = field(
        default=".",
        metadata={
            "description": "用户上传的文件存储到这个根目录下"
        },
    )

    query_model: Annotated[str, {"__template_metadata__": {"kind": "llm"}}] = field(
        default="openai/Qwen2.5-14B-Instruct",
        metadata={
            "description": "处理和优化查询的模型. 以下列格式提供: provider/model-name."
        },
    )
