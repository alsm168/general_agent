"""Research Agent Implementation.

This module implements a research agent that can perform iterative web searches
and synthesis to answer complex research questions.
"""

from multiprocessing import synchronize
from pydantic import BaseModel, Field
from typing_extensions import Literal

from langgraph.graph import StateGraph, START, END
from langchain_core.messages import SystemMessage, HumanMessage, ToolMessage, filter_messages, AIMessage
from shared.tools import think_tool
from shared.utils import load_chat_model
from travel_agent.state import MapState
from travel_agent.tools import get_mcp_tools
from travel_agent.configuration import MapConfiguration
from travel_agent.prompts import map_agent_prompt, answer_prompt
from langgraph.types import Command
from langgraph.prebuilt import ToolNode
import asyncio

# ===== CONFIGURATION =====

# Set up tools and model binding

tools = asyncio.run(get_mcp_tools())  + [think_tool]
model = load_chat_model(MapConfiguration().query_model)
model_with_tools = model.bind_tools(tools)


# ===== AGENT NODES =====

async def llm_call(state: MapState):
    """分析当前状态并决定下一步操作。

    模型会分析当前的对话状态，并决定是：
    1. 调用MAP工具以收集更多信息
    2. 根据已收集的信息提供最终答案

    返回包含模型响应的更新后的状态。
    """
    response = model_with_tools.invoke(
                [SystemMessage(content=map_agent_prompt)] + state["map_messages"]
            )
    tool_call_iterations = state.get("tool_call_iterations", 0)
    if response.tool_calls:
        tool_call_iterations = tool_call_iterations + 1
        if tool_call_iterations > MapConfiguration().tool_call_iteration_limit:
            return Command(
                goto="get_search_result",
                update={"map_messages": [AIMessage(content="工具使用次数达到上限，请按现有内容回答问题")], "tool_call_iterations": tool_call_iterations}
            )

    return {
        "map_messages": [response],
        "tool_call_iterations": tool_call_iterations
    }

def get_map_result(state: MapState) -> dict:
    """
    根据map_messages获取搜索结果
    """
    map_messages = state.get("map_messages", [])
    if map_messages[-1].type == 'ai':
        messages = [SystemMessage(content=answer_prompt)] + map_messages + [HumanMessage(content="请根据以上结果回答问题")]
    else:
        messages = [SystemMessage(content=answer_prompt)] + map_messages
    
    response = model.invoke(messages)

    return {
        "map_messages": [response],
        "map_result": str(response.content),
    }

# ===== ROUTING LOGIC =====

def should_continue(state: MapState) -> Literal["tool_node", "get_map_result"]:
    """判断是否继续检索或给出最终答案。

    根据大语言模型（LLM）是否发起工具调用，判断代理应该继续检索循环还是给出最终答案。

    返回值:
        "tool_node": 继续执行工具调用
        "get_map_result": 停止并给出最终答案
    """
    messages = state["map_messages"]
    last_message = messages[-1]

    # If the LLM makes a tool call, continue to tool execution
    if last_message.tool_calls:
        return "tool_node"
    # Otherwise, we have a final answer
    return 'get_map_result'

builder = StateGraph(MapState, input=MapState, config_schema=MapConfiguration)
builder.add_node(llm_call)
builder.add_node('tool_node', ToolNode(tools=tools, messages_key="map_messages"))
builder.add_node(get_map_result)
builder.add_edge(START, "llm_call")
builder.add_conditional_edges(
    "llm_call",
    should_continue,
    {
        "tool_node": "tool_node",
        "get_map_result": "get_map_result"
    }
)
builder.add_edge("tool_node", "llm_call")
builder.add_edge("get_map_result", END)

# Finally, we compile it!
# This compiles it into a graph you can invoke and deploy.
graph = builder.compile()
graph.name = "TravelAgentGraph"
