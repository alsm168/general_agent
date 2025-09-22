"""Main entrypoint for the conversational retrieval graph.

This module defines the core structure and functionality of the conversational
retrieval graph. It includes the main graph definition, state management,
and key functions for processing user inputs, generating queries, retrieving
relevant documents, and formulating responses.
"""

from datetime import datetime, timezone

from typing import Any, Literal, TypedDict, cast
from langchain_core.documents import Document
from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate
from langgraph.checkpoint.serde.types import C
from pydantic import BaseModel
from langchain_core.runnables import RunnableConfig
from langgraph.graph import StateGraph, START, END
from langgraph.types import interrupt, Command

from shared import retrieval
from retrieval_graph.configuration import Configuration
from retrieval_graph.state import InputState, State
from shared.utils import format_docs, get_message_text, load_chat_model

# Define the function that calls the model


class SearchQuery(BaseModel):
    """Search the indexed documents for a query."""

    query: str


async def generate_query(
    state: State, *, config: RunnableConfig
) -> dict[str, list[str]]:
    """基于当前状态和配置生成搜索查询。

    此函数分析状态中的消息并生成合适的搜索查询。对于第一条消息，它直接使用用户输入。
    对于后续消息，它使用语言模型生成优化后的查询。

    参数:
        state (State): 包含消息和其他信息的当前状态。
        config (RunnableConfig | None, optional): 查询生成过程的配置。

    返回:
        dict[str, list[str]]: 一个字典，包含键 'queries'，其值为生成的查询列表。

    行为:
        - 如果只有一条消息（首次用户输入），则直接使用该消息作为查询。
        - 对于后续消息，使用语言模型生成优化后的查询。
        - 该函数使用配置来设置查询生成的提示词和模型。
    """
    messages = state.messages
    if len(messages) == 1:
        # It's the first user question. We will use the input directly to search.
        human_input = get_message_text(messages[-1])
        return {"queries": [human_input]}
    else:
        configuration = Configuration.from_runnable_config(config)
        # Feel free to customize the prompt, model, and other logic!
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", configuration.query_system_prompt),
                ("placeholder", "{messages}"),
            ]
        )
        model = load_chat_model(configuration.query_model).with_structured_output(
            SearchQuery
        )

        message_value = await prompt.ainvoke(
            {
                "messages": state.messages,
                "queries": "\n- ".join(state.queries),
                "system_time": datetime.now(tz=timezone.utc).isoformat(),
            },
            config,
        )
        generated = cast(SearchQuery, await model.ainvoke(message_value, config))
        return {
            "queries": [generated.query],
        }


async def retrieve(
    state: State, *, config: RunnableConfig
) -> dict[str, list[Document]]:
    """基于状态中的最新查询检索文档。

    此函数接收当前状态和配置，使用状态中的最新查询，通过RAG检索器检索相关文档，
    并返回检索到的文档。

    参数:
        state (State): 包含查询和检索器的当前状态。
        config (RunnableConfig | None, 可选): 检索过程的配置。

    返回:
        dict[str, list[Document]]: 一个字典，包含单个键 "retrieved_docs"，
        其值为检索到的 Document 对象列表。
    """
    print(f"retrieve state: {state} ************************************")
    with retrieval.make_retriever(config) as retriever:
        response = await retriever.ainvoke(state.queries[-1], config)
        return {"retrieved_docs": response}


async def respond(
    state: State, *, config: RunnableConfig
) -> dict[str, list[BaseMessage]]:
    """
    基于状态中的消息和检索到的文档生成响应。

    此函数接收当前状态和配置，使用状态中的消息和检索到的文档，通过语言模型生成响应。
    它使用配置来设置响应生成的提示词和模型。

    参数:
        state (State): 包含消息、检索到的文档和其他信息的当前状态。
        config (RunnableConfig | None, 可选): 响应生成过程的配置。

    返回:
        dict[str, list[BaseMessage]]: 一个字典，包含单个键 "messages"，
        其值为生成的响应消息列表。
    """
    configuration = Configuration.from_runnable_config(config)
    # Feel free to customize the prompt, model, and other logic!
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", configuration.response_system_prompt),
            ("placeholder", "{messages}"),
        ]
    )
    model = load_chat_model(configuration.response_model)

    retrieved_docs = format_docs(state.retrieved_docs)
    message_value = await prompt.ainvoke(
        {
            "messages": state.messages,
            "retrieved_docs": retrieved_docs,
            "system_time": datetime.now(tz=timezone.utc).isoformat(),
        },
        config,
    )
    response = await model.ainvoke(message_value, config)
    # We return a list, because this will get added to the existing list
    return {"messages": [response]}


# Define a new graph (It's just a pipe)


builder = StateGraph(State, input=InputState, config_schema=Configuration)

builder.add_node(generate_query)
builder.add_node(retrieve)
builder.add_node(respond)
builder.add_edge(START, "generate_query")
builder.add_edge("generate_query", "retrieve")
builder.add_edge("retrieve", "respond")
builder.add_edge("respond", END)

from langgraph.checkpoint.memory import InMemorySaver
# Finally, we compile it!
# This compiles it into a graph you can invoke and deploy.
graph = builder.compile(
    # checkpointer=InMemorySaver(),  # 添加检查点以支持中断功能
    # interrupt_before=["human_action"],  # 在执行操作前中断等待人工审批
)
graph.name = "RetrievalGraph"
