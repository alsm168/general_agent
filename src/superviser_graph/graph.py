"""Main entrypoint for the conversational retrieval graph.

This module defines the core structure and functionality of the conversational
retrieval graph. It includes the main graph definition, state management,
and key functions for processing & routing user queries, generating research plans to answer user questions,
conducting research, and formulating responses.
"""

import uuid

from typing import Any, Literal, TypedDict, cast

from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.runnables import RunnableConfig
from langgraph.graph import END, START, StateGraph
from langgraph.types import interrupt, Command
from langgraph.store.memory import InMemoryStore
from langgraph.checkpoint.memory import InMemorySaver
from langgraph.config import get_store

from researcher_agent.graph import graph as researcher_agent_graph
from file_agent.graph import graph as file_agent_graph
from address_book_agent.graph import graph as address_book_agent_graph
from web_search_agent.graph import graph as web_search_agent_graph
from retrieval_graph.graph import graph as retrieval_agent
from travel_agent.graph import graph as travel_agent_graph

from superviser_graph.configuration import AgentConfiguration
from superviser_graph.state import AgentState, InputState, Router, UserInformation
from shared.utils import format_docs, load_chat_model
from shared.retrieval import make_text_encoder



async def analyze_and_route_query(
    state: AgentState, *, config: RunnableConfig
) -> dict[str, Router]:
    """分析用户的查询并确定合适的路由。

    此函数使用语言模型对用户的查询进行分类，并决定在对话流程中如何路由该查询。

    参数:
        state (AgentState): 代理的当前状态，包括对话历史。
        config (RunnableConfig): 包含用于查询分析的模型的配置。

    返回:
        dict[str, Router]: 一个字典，包含 'router' 键，其值为分类结果（分类类型和逻辑）。
    """

    # 如果输入包含了文件路径，那么判断为file_question
    if state.messages[-1].additional_kwargs.get("file_path"):
        return {"router": Router(type="file_question", logic=state.messages[-1].additional_kwargs.get("file_path"))}
    elif state.choose_web_search:
        return {"router": Router(type="web_search", logic="用户选择了网页搜索")}
    
    # 其他判断
    configuration = AgentConfiguration.from_runnable_config(config)
    model = load_chat_model(configuration.query_model)
    messages = [
        {"role": "system", "content": configuration.router_system_prompt},
        *state.messages
    ]
    response = cast(
        Router, await model.with_structured_output(Router).ainvoke(messages)
    )
    if response.logic == "address_book":
        response.type = "address_book"
    return {"router": response}

async def propose_action(state: AgentState, *, config: RunnableConfig) -> AgentState:
    """ 
    提出一个需要人工审批的操作

    参数:
        state (AgentState): 代理的当前状态，包括对话历史和路由信息。
        config (RunnableConfig): 包含用于查询分析的模型的配置。

    返回:
        AgentState: 更新后的状态，包含提出的操作详情。
    """
    return {"proposed_action_details": f" 请审批下列意图分类 '{state.router.type}'与分类原因'{state.router.logic} '"}

async def human_approval_node(state: AgentState, *, config: RunnableConfig) -> Command[Literal["execute_action"]]:
    """ 
    在执行关键行动前请求人工审批

    参数:
        state (AgentState): 代理的当前状态，包括对话历史和路由信息。
        config (RunnableConfig): 包含用于查询分析的模型的配置。

    返回:
        Command[Literal["execute_action"]]: 一个命令，指示是否继续执行操作。
    """
    # 待审批操作的详情
    approval_request = interrupt(
        {
            "question": f"请问同意这个意图分类 '{state.router.type}'与分类原因'{state.router.logic} '吗?不同意，请选择您需要的分类(file_question, address_book, more-info, langchain, general, web_search, langgraph)",
        })

    if approval_request["user_response"] == "approve": 
        # 用户批准
        return Command(goto="execute_action") # 路由到执行操作的节点
    else: # 用户拒绝
        return Command(goto="execute_action", update={"router": Router(type=approval_request["type"], logic="用户选择的分类")}) # 路由到修改操作的节点

async def execute_action(state: AgentState, *, config: RunnableConfig) -> AgentState:
    """ 
    执行已批准的操作

    参数:
        state (AgentState): 代理的当前状态，包括对话历史和路由信息。
        config (RunnableConfig): 包含用于查询分析的模型的配置。

    返回:
        AgentState: 更新后的状态，包含执行操作的详情。
    """
    return {"proposed_action_details": f"意图分类 '{state.router.type}'与分类原因'{state.router.logic} '已经被人工审核批准"}


def route_query(
    state: AgentState,
) -> Literal["researcher_agent", "ask_for_more_info", "respond_to_general_query", "file_agent", "retrieval_agent", "address_book_agent", "conduct_web_search", "conduct_travel_search"]:
    """ 
    根据查询分类确定下一个步骤

    参数:
        state (AgentState): 代理的当前状态，包括对话历史和路由信息。

    返回:
        Literal["researcher_agent", "ask_for_more_info", "respond_to_general_query", "file_agent", "retrieval_agent", "address_book_agent", "conduct_web_search", "conduct_travel_search" ]: 下一个要执行的步骤。

    抛出:
        ValueError: 如果遇到未知的路由类型。
    注意：新增类型，需要同时修改prompt、Router定义，以及本函数的返回值
    """
    router = state.router
    _type = router.type
    if _type == "langchain":
        return "retrieval_agent"
    elif _type == "langgraph":
        return "researcher_agent"
    elif _type == "more-info":
        return "ask_for_more_info"
    elif _type == "file_question":
        return "file_agent"
    elif _type == "address_book":
        return "address_book_agent"
    elif _type == "web_search":
        return "conduct_web_search"
    elif _type == "travel":
        return "conduct_travel_search"
    elif _type == "general":
        return "respond_to_general_query"
    else:
        raise ValueError(f"Unknown router type {_type}")


async def ask_for_more_info(
    state: AgentState, *, config: RunnableConfig
) -> dict[str, list[BaseMessage]]:
    """ 
    生成一个要求用户提供更多信息的响应

    当路由确定需要从用户那里获取更多信息时，会调用此节点。

    参数:
        state (AgentState): 代理的当前状态，包括对话历史和路由信息。
        config (RunnableConfig): 包含用于查询分析的模型的配置。

    返回:
        dict[str, list[BaseMessage]]: 包含生成响应的 'messages' 键的字典。
    """
    configuration = AgentConfiguration.from_runnable_config(config)
    model = load_chat_model(configuration.query_model)
    system_prompt = configuration.more_info_system_prompt.format(
        logic=state.router.logic
    )
    messages = [{"role": "system", "content": system_prompt}] + state.messages
    response = await model.ainvoke(messages)
    return {"messages": [response]}


async def respond_to_general_query(
    state: AgentState, *, config: RunnableConfig
) -> dict[str, list[BaseMessage]]:
    """ 
    生成一个响应，用于回答与LangChain无关的一般查询。

    当路由将查询分类为一般问题时，会调用此节点。

    参数:
        state (AgentState): 代理的当前状态，包括对话历史和路由信息。
        config (RunnableConfig): 包含用于查询分析的模型的配置。

    返回:
        dict[str, list[BaseMessage]]: 包含生成响应的 'messages' 键的字典。
    """
    configuration = AgentConfiguration.from_runnable_config(config)
    model = load_chat_model(configuration.query_model)
    system_prompt = configuration.general_system_prompt.format(
        logic=state.router.logic
    )
    messages = [{"role": "system", "content": system_prompt}] + state.messages
    response = await model.ainvoke(messages)
    return {"messages": [response]}

async def conduct_web_search(state: AgentState, *, config: RunnableConfig) -> dict[str, Any]:
    """ 
    执行研究计划中的网络搜索步骤

    此函数获取研究计划中的第一个步骤，并使用它进行网络搜索。

    参数:
        state (AgentState): 代理的当前状态，包括研究计划的步骤。
        config (RunnableConfig): 包含用于查询分析的模型的配置。

    返回:
        dict[str, list[str]]: 包含 'documents' 键的字典，其中包含搜索结果，
                              'steps' 键包含剩余的研究步骤。

    行为:
        - 调用 web_search_agent 并传入研究计划中的第一个步骤。
        - 更新状态，包含检索到的文档和移除已完成的步骤。
    """
    result = await web_search_agent_graph.ainvoke({"web_search_messages": [state.messages[-1]]}, config=config)
    return {"messages": [AIMessage(content=result["web_search_result"])]}

async def conduct_travel_search(state: AgentState, *, config: RunnableConfig) -> dict[str, Any]:
    """ 
    执行旅行规划中的搜索分析步骤

    参数:
        state (AgentState): 代理的当前状态，包括旅行的问题。
        config (RunnableConfig): 包含用于查询分析的模型的配置。

    返回:
        dict[str, list[str]]: 包含 'map_result' 键的字典，其中包含旅行规划结果。

    行为:
        - 调用 travel_agent 并传入旅行问题。
        - 更新状态，包含检索到的旅行规划结果。
    """
    result = await travel_agent_graph.ainvoke({"map_messages": [state.messages[-1]]}, config=config)
    return {"messages": [AIMessage(content=result["map_result"])]}

async def memory_node(state: AgentState, config: RunnableConfig) -> AgentState:
    """
    从当前状态中提取需要存储在内存中的信息
    
    参数:
        state: 当前代理状态
        config: 运行配置
        
    返回:
        更新后的状态，包含检索结果
    """
    configuration = AgentConfiguration.from_runnable_config(config)
    print(f"config: {config}")
    user_name = config["configurable"].get("user_name", 'unkown')

    model = load_chat_model(configuration.query_model).with_structured_output(UserInformation)
    system_prompt = configuration.memory_system_prompt.format(
        user_name=user_name
    )
    messages = [{"role": "system", "content": system_prompt}] + state.messages
    response = cast(UserInformation, await model.ainvoke(messages))

    store = get_store()

    key_word = uuid.uuid4()
    if response.interest and response.interest!='无':
        store.put((user_name, "interest"), key_word, {"text": response.interest})
    
    if response.specialization and response.specialization!='无':
        store.put((user_name, "specialization"), key_word, {"text": response.specialization})
    
    interest = store.get((user_name, "interest"), key_word)
    specialization = store.get((user_name, "specialization"), key_word)
    print(f"interest: {interest}")
    print(f"specialization: {specialization}")

    return Command(goto=END)

# Define the graph
builder = StateGraph(AgentState, input=InputState, config_schema=AgentConfiguration)
builder.add_node(analyze_and_route_query)
builder.add_node(ask_for_more_info)
builder.add_node(respond_to_general_query)
builder.add_node(conduct_web_search)
builder.add_node(conduct_travel_search)
builder.add_node(propose_action)
builder.add_node(human_approval_node)
builder.add_node(execute_action)
builder.add_node(memory_node)



builder.add_node("retrieval_agent", retrieval_agent)
builder.add_node("researcher_agent", researcher_agent_graph)
builder.add_node("file_agent", file_agent_graph)
builder.add_node("address_book_agent", address_book_agent_graph)



builder.add_edge(START, "analyze_and_route_query")
builder.add_edge("analyze_and_route_query", "propose_action")
builder.add_edge("propose_action", "human_approval_node")
builder.add_conditional_edges("execute_action", route_query)

builder.add_edge("ask_for_more_info", END)
builder.add_edge("respond_to_general_query", END)
builder.add_edge("address_book_agent", 'memory_node')
builder.add_edge("file_agent", 'memory_node')
builder.add_edge("researcher_agent", 'memory_node')
builder.add_edge("conduct_web_search", 'memory_node')
builder.add_edge("retrieval_agent", 'memory_node')
builder.add_edge("conduct_travel_search", 'memory_node')
builder.add_edge('memory_node', END)

# initiate store with long memory
embeddings = make_text_encoder(AgentConfiguration.embedding_model)
store = InMemoryStore(
    index={
        "embed": embeddings,
        "dims": 1024,
    }
)

# Compile into a graph object that you can invoke and deploy.
graph = builder.compile(checkpointer=InMemorySaver(), store=store)
graph.name = "SupervisorGraph"
