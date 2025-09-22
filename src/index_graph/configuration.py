"""Define the configurable parameters for the index graph."""

from __future__ import annotations

from dataclasses import dataclass, field

from shared.configuration import BaseConfiguration

# This file contains sample documents to index, based on the following LangChain and LangGraph documentation pages:
# - https://python.langchain.com/v0.3/docs/concepts/
# - https://langchain-ai.github.io/langgraph/concepts/low_level/
DEFAULT_DOCS_FILE = "src/sample_docs.json"


@dataclass(kw_only=True)
class IndexConfiguration(BaseConfiguration):
    """用于RAG向量数据库索引和检索操作的配置类。

    此类定义了配置索引和检索过程所需的参数，包括嵌入模型选择、检索器提供者选择和搜索参数。
    """

    docs_file: str = field(
        default=DEFAULT_DOCS_FILE,
        metadata={
            "description": "Path to a JSON file containing default documents to index."
        },
    )
