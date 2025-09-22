"""State management for the retrieval graph.

This module defines the state structures used in the retrieval graph. It includes
definitions for agent state, input state, and router classification schema.
"""

from dataclasses import dataclass, field
from typing import Annotated, Literal, TypedDict

from langchain_core.documents import Document
from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages
from shared.state import reduce_docs


@dataclass(kw_only=True)
class FileAgentState:
    """FileAgent的状态类。

    此类定义了FileAgent的状态结构，包括消息、索引名称和文档列表。
    """

    messages: Annotated[list[AnyMessage], add_messages]

    documents: Annotated[list[Document], reduce_docs] = field(default_factory=list)
    """由检索器填充。这是一个代理可以参考的文档列表。"""
