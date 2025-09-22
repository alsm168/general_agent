"""This "graph" simply exposes an endpoint for a user to upload docs to be indexed."""

import json
from typing import Optional

from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph

from index_graph.configuration import IndexConfiguration
from index_graph.state import IndexState
from shared import retrieval
from shared.state import reduce_docs


async def index_docs(
    state: IndexState, *, config: Optional[RunnableConfig] = None
) -> dict[str, str]:
    """使用配置好的检索器异步索引给定状态中的文档。

    此函数从状态中获取文档，确保文档包含用户 ID，
    将它们添加到检索器的索引中，然后发出信号从状态中删除这些文档。

    如果状态中未提供文档，则会从 configuration.docs_file 指定的 JSON 文件中加载文档。

    参数:
        state (IndexState): 包含文档和检索器的当前状态。
        config (Optional[RunnableConfig]): 索引过程的配置。
    """
    if not config:
        raise ValueError("Configuration required to run index_docs.")

    configuration = IndexConfiguration.from_runnable_config(config)
    docs = state.docs
    if not docs:
        with open(configuration.docs_file) as f:
            serialized_docs = json.load(f)
            docs = reduce_docs([], serialized_docs)

    with retrieval.make_retriever(config) as retriever:
        await retriever.aadd_documents(docs)

    return {"docs": "delete"}


# Define the graph
builder = StateGraph(IndexState, config_schema=IndexConfiguration)
builder.add_node(index_docs)
builder.add_edge(START, "index_docs")
builder.add_edge("index_docs", END)
# Compile into a graph object that you can invoke and deploy.
graph = builder.compile()
graph.name = "IndexGraph"
