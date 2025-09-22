"""Define the configurable parameters for the file agent."""

from __future__ import annotations

from dataclasses import dataclass, field

from shared.configuration import BaseConfiguration

from typing import Annotated

from address_book_agent import prompts


@dataclass(kw_only=True)
class AddressBookAgentConfiguration(BaseConfiguration):
    """
    用于AddressBookAgent的配置类。
    此类定义了配置AddressBookAgent所需的参数，包括采用的模型
    """

    query_model: Annotated[str, {"__template_metadata__": {"kind": "llm"}}] = field(
        default="openai/Qwen2.5-14B-Instruct",
        metadata={
            "description": "处理和优化查询的模型. 以下列格式提供: provider/model-name."
        },
    )

    query_system_prompt: str = field(
        default=prompts.QUERY_SYSTEM_PROMPT,
        metadata={
            "description": "The system prompt used for processing and refining queries."
        },
    )

    response_system_prompt: str = field(
        default=prompts.RESPONSE_SYSTEM_PROMPT,
        metadata={"description": "The system prompt used for generating responses."},
    )
