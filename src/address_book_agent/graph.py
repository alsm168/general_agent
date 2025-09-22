from datetime import datetime, timezone
from turtle import update
from typing import cast, Literal
import pandas as pd
from langchain_core.messages import BaseMessage
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.runnables import RunnableConfig
from langchain_experimental.agents import create_pandas_dataframe_agent
from langgraph.graph import StateGraph, START, END
from langgraph.types import Command
from shared.utils import load_chat_model, get_message_text
from address_book_agent.configuration import AddressBookAgentConfiguration
from address_book_agent.state import State, ThinkContent, SearchQuery
from address_book_agent.prompts import THINK_PROMPT


async def generate_query(
    state: State, *, config: RunnableConfig
) -> dict[str, list[str]]:
    """基于当前状态和配置生成搜索查询。

    此函数分析状态中的消息并生成合适的搜索查询。对于第一条消息，它直接使用用户输入。
    对于后续消息，它使用语言模型生成优化后的查询。

    参数:
        state (State): 当前状态，包含消息和其他信息。
        config (RunnableConfig | None, 可选): 查询生成过程的配置。

    返回:
        dict[str, list[str]]: 一个字典，包含键 'queries'，对应一个生成的查询列表。

    行为:
        - 如果只有一条消息（首次用户输入），则将其用作查询。
        - 对于后续消息，使用语言模型生成优化后的查询。
        - 函数使用配置来设置查询生成的提示词和模型。
    """
    messages = state.messages
    if len(messages) == 1:
        # It's the first user question. We will use the input directly to search.
        human_input = get_message_text(messages[-1])
        return {"queries": [human_input]}
    else:
        configuration = AddressBookAgentConfiguration.from_runnable_config(config)
        # Feel free to customize the prompt, model, and other logic!
        prompt = ChatPromptTemplate.from_messages(
            [
                ("system", configuration.query_system_prompt),
                ("placeholder", "{messages}"),
            ]
        )
        model = load_chat_model(AddressBookAgentConfiguration.from_runnable_config(config).query_model).with_structured_output(
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
) -> dict[str, list[str]]:
    """从通讯录样本中检索文档.

    参数:
        state (State): 包含查询和检索器的当前状态。
        config (RunnableConfig | None, 可选): 检索过程的配置。

    返回:
        dict[str, list[str]]: 一个字典，包含单个键 "retrieved_books"，
        对应一个包含检索结果的字符串列表。
    """
    # 1. 读取 Excel
    df = pd.read_excel("/mnt/sdb/data/audio/文档样本/oa/通讯录样本.xlsx")

    # 2. 创建 Agent
    llm = load_chat_model(AddressBookAgentConfiguration.from_runnable_config(config).query_model)
    pandas_agent = create_pandas_dataframe_agent(llm, df,  allow_dangerous_code=True) # verbose=True,

    # 3. 提问（自然语言）
    response = await pandas_agent.ainvoke(state.queries[-1])
    return {"retrieved_books": [response.get("output")]}


async def think(state: State, *, config: RunnableConfig) -> Command[Literal["respond", "generate_query"]]:
    """
    思考当前状态并生成思考内容.

    此函数根据当前状态和配置，使用语言模型生成思考内容。如果需要检索文档，
    它会返回一个命令，指示生成查询。否则，它会返回一个命令，指示直接响应。

    参数:
        state (State): 当前状态，包含消息、查询和检索到的文档。
        config (RunnableConfig | None, 可选): 思考过程的配置。

    返回:
        Command[Literal["respond", "generate_query"]]: 一个命令，指示下一步要执行的操作。

    行为:
        - 使用配置中的模型和提示词生成思考内容。
        - 如果生成的思考内容指示需要检索文档，返回 "generate_query" 命令。
        - 否则，返回 "respond" 命令。
    """
    configuration = AddressBookAgentConfiguration.from_runnable_config(config)

    retrieved_docs = "\n\n".join(state.retrieved_books)
    if state.think_count >= 1: # 确保只思考一次
        return Command(
            goto="respond",
        )

    messages = [
        {"role": "system", "content": THINK_PROMPT},
        {"role": "user", "content": f"用户询问的问题是 {state.queries[-1]}\n当前搜索结果: {retrieved_docs}"}
    ]
    model = load_chat_model(configuration.query_model).with_structured_output(
        ThinkContent
    )
    response = cast(ThinkContent, await model.ainvoke(messages))
    
    if response.need_retrive:
        return Command(
            goto="generate_query",
            update={"think_content": response, "think_count": 1},
        )
    else:
        return Command(
            goto="respond",
            update={"think_content": response, "think_count": 1},
        )

async def respond(
    state: State, *, config: RunnableConfig
) -> dict[str, list[BaseMessage]]:
    """
    生成响应.

    此函数根据当前状态和配置，使用语言模型生成响应。它使用配置中的提示词和模型，
    并将当前消息、检索到的文档和系统时间作为输入。

    参数:
        state (State): 当前状态，包含消息、查询和检索到的文档。
        config (RunnableConfig | None, 可选): 响应生成过程的配置。

    返回:
        dict[str, list[BaseMessage]]: 一个字典，包含一个键 "messages"，
        对应一个包含生成响应的 BaseMessage 对象的列表。

    行为:
        - 使用配置中的模型和提示词生成响应。
        - 将当前消息、检索到的文档和系统时间作为输入。
        - 返回一个包含生成响应的 BaseMessage 对象的列表。
    """
    configuration = AddressBookAgentConfiguration.from_runnable_config(config)
    # Feel free to customize the prompt, model, and other logic!
    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", configuration.response_system_prompt),
            ("placeholder", "{messages}"),
        ]
    )
    model = load_chat_model(configuration.query_model)

    retrieved_docs = "\n\n".join(state.retrieved_books)
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


# Define a new graph
# 注意，本图与主图共享messages消息
builder = StateGraph(State, input=State, config_schema=AddressBookAgentConfiguration)
builder.add_node(generate_query)
builder.add_node(retrieve)
builder.add_node(think)
builder.add_node(respond)
builder.add_edge("__start__", "generate_query")
builder.add_edge("generate_query", "retrieve")
builder.add_edge("retrieve", "think")
builder.add_edge("respond", END)

# Finally, we compile it!
# This compiles it into a graph you can invoke and deploy.
graph = builder.compile()
graph.name = "AddressBookAgentGraph"
