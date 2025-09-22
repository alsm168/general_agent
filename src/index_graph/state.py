"""State management for the index graph."""

from dataclasses import dataclass
from typing import Annotated

from langchain_core.documents import Document

from shared.state import reduce_docs


# The index state defines the simple IO for the single-node index graph
@dataclass(kw_only=True)
class IndexState:
    """表示文档索引和检索的状态。

    此类定义了索引状态的结构，其中包括要索引的文档以及用于搜索这些文档的检索器。
    """

    docs: Annotated[list[Document], reduce_docs]
    """A list of documents that the agent can index."""
