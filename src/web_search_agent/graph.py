"""Research Agent Implementation.

This module implements a research agent that can perform iterative web searches
and synthesis to answer complex research questions.
"""

from pydantic import BaseModel, Field
from typing_extensions import Literal

from langgraph.graph import StateGraph, START, END
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage, filter_messages, AIMessage
from shared.tools import think_tool
from shared.utils import load_chat_model
from web_search_agent.state import WebSearchState
from web_search_agent.tools import tavily_search
from web_search_agent.configuration import WebSearchConfiguration
from web_search_agent.prompts import research_agent_prompt, answer_prompt
from langgraph.types import Command

# ===== CONFIGURATION =====

# Set up tools and model binding
tools = [tavily_search, think_tool]
tools_by_name = {tool.name: tool for tool in tools}

model = load_chat_model(WebSearchConfiguration().query_model)
model_with_tools = model.bind_tools(tools)


# ===== AGENT NODES =====

def llm_call(state: WebSearchState):
    """分析当前状态并决定下一步操作。

    模型会分析当前的对话状态，并决定是：
    1. 调用搜索工具以收集更多信息
    2. 根据已收集的信息给出最终答案
    3. 如果工具调用次数超过限制，返回最终答案
    4. 如果模型没有发起工具调用，且没有收到工具调用的结果，返回最终答案

    返回包含模型响应的更新后的状态。
    """
    print(r'llm_call:', state)
    response = model_with_tools.invoke(
                [SystemMessage(content=research_agent_prompt)] + state["web_search_messages"]
            )
    print(r'llm_call:', response)
    tool_call_iterations = state.get("tool_call_iterations", 0)
    if response.tool_calls:
        tool_call_iterations = tool_call_iterations + 1
        if tool_call_iterations > WebSearchConfiguration().tool_call_iteration_limit:
            return Command(
                goto="get_search_result",
                update={"web_search_messages": [AIMessage(content="工具使用次数达到上限，请按现有内容回答问题")], "tool_call_iterations": tool_call_iterations}
            )

    return {
        "web_search_messages": [response],
        "tool_call_iterations": tool_call_iterations
    }

def tool_node(state: WebSearchState):
    """执行上一次大语言模型(LLM)响应中的所有工具调用。

    执行上一次LLM响应中的所有工具调用，返回包含工具执行结果的更新后状态。
    """
    print(r'tool_node:', state)
    tool_calls = state["web_search_messages"][-1].tool_calls

    # Execute all tool calls
    observations = []
    for tool_call in tool_calls:
        tool = tools_by_name[tool_call["name"]]
        observations.append(tool.invoke(tool_call["args"]))

    # Create tool message outputs
    tool_outputs = [
        ToolMessage(
            content=observation,
            name=tool_call["name"],
            tool_call_id=tool_call["id"]
        ) for observation, tool_call in zip(observations, tool_calls)
    ]
    return {"web_search_messages": tool_outputs}

def get_search_result(state: WebSearchState) -> dict:
    """
    根据web_search_messages获取搜索结果
    """
    web_search_messages = state.get("web_search_messages", [])
    if web_search_messages[-1].type == 'ai':
        messages = [SystemMessage(content=answer_prompt)] + web_search_messages + [HumanMessage(content="请根据以上搜索结果回答问题")]
    else:
        messages = [SystemMessage(content=answer_prompt)] + web_search_messages
    
    response = model.invoke(messages)

    return {
        "web_search_messages": [response],
        "web_search_result": str(response.content),
    }

# ===== ROUTING LOGIC =====

def should_continue(state: WebSearchState) -> Literal["tool_node", "get_search_result"]:
    """判断是继续研究还是给出最终答案。

    根据大语言模型(LLM)是否发起了工具调用，判断智能体是应该继续研究循环，还是给出最终答案。

    返回值:
        "tool_node": 继续执行工具调用
        "get_search_result": 停止研究并获取搜索结果
    """
    messages = state["web_search_messages"]
    last_message = messages[-1]

    # If the LLM makes a tool call, continue to tool execution
    if last_message.tool_calls:
        return "tool_node"
    # Otherwise, we have a final answer
    return 'get_search_result'

builder = StateGraph(WebSearchState, input=WebSearchState, config_schema=WebSearchConfiguration)
builder.add_node(llm_call)
builder.add_node(tool_node)
builder.add_node(get_search_result)
builder.add_edge("__start__", "llm_call")
builder.add_conditional_edges(
    "llm_call",
    should_continue,
    {
        "tool_node": "tool_node",
        "get_search_result": "get_search_result"
    }
)
builder.add_edge("tool_node", "llm_call")
builder.add_edge("get_search_result", END)

# Finally, we compile it!
# This compiles it into a graph you can invoke and deploy.
graph = builder.compile()
graph.name = "WebSearchAgentGraph"
