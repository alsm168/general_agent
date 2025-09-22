"""Researcher graph used in the conversational retrieval system as a subgraph.

This module defines the core structure and functionality of the researcher graph,
which is responsible for generating search queries and retrieving relevant documents.
"""
from typing import Any, Literal, TypedDict, cast

from langchain_core.runnables import RunnableConfig
from langchain_core.messages import AIMessage, BaseMessage, HumanMessage
from langgraph.graph import END, START, StateGraph

from researcher_agent.configuration import ResearcherConfiguration
from researcher_agent.state import SuperviserState
from researcher_agent.sub_graph import graph as researcher_graph
from shared.utils import load_chat_model, format_docs


async def create_research_plan(
    state: SuperviserState, *, config: RunnableConfig
) -> dict[str, list[str] | str]:
    """Create a step-by-step research plan for answering a LangChain-related query.

    Args:
        state (AgentState): The current state of the agent, including conversation history.
        config (RunnableConfig): Configuration with the model used to generate the plan.

    Returns:
        dict[str, list[str]]: A dictionary with a 'steps' key containing the list of research steps.
    """

    class Plan(TypedDict):
        """Generate research plan."""

        steps: list[str]

    configuration = ResearcherConfiguration.from_runnable_config(config)
    model = load_chat_model(configuration.query_model).with_structured_output(Plan)
    messages = [
            {"role": "system", "content": configuration.research_plan_system_prompt}
        ] + state.messages
    response = cast(Plan, await model.ainvoke(messages))
    return {"steps": response["steps"], "documents": "delete"}

# def propose_action(state: SuperviserState) -> SuperviserState:
#     """ 提出一个需要人工审批的操作 """
#     steps_str = "\n".join(state.steps)
#     return {"proposed_action_details": f" 请审批下列研究计划 '{steps_str}' "}

# def human_approval_node(state: SuperviserState) -> Command[Literal["execute_action", "revise_action"]]:
#     """ 在执行关键行动前请求人工审批 """
#     # 待审批操作的详情
#     approval_request = interrupt(
#         {
#             "question": "请问同意这个研究计划吗?",
#             "action_details": state["proposed_action_details"]
#         })

#     if approval_request["user_response"] == "approve": 
#         # 用户批准
#         return Command(goto="execute_action") # 路由到执行操作的节点
#     else: # 用户拒绝
#         return Command(goto="revise_action") # 路由到修改操作的节点

# def execute_action(state: SuperviserState) -> SuperviserState:
#     """ 执行已批准的操作 """
#     return {"proposed_action_details": f"研究计划已经被人工审核批准"}

# def revise_action(state: SuperviserState) -> SuperviserState:
#     """ 修改被拒绝的操作 """
#     return {"proposed_action_details": f"需要重新修改计划"}

async def conduct_research(state: SuperviserState, *, config: RunnableConfig) -> dict[str, Any]:
    """Execute the first step of the research plan.

    This function takes the first step from the research plan and uses it to conduct research.

    Args:
        state (AgentState): The current state of the agent, including the research plan steps.

    Returns:
        dict[str, list[str]]: A dictionary with 'documents' containing the research results and
                              'steps' containing the remaining research steps.

    Behavior:
        - Invokes the researcher_graph with the first step of the research plan.
        - Updates the state with the retrieved documents and removes the completed step.
    """
    # 【关键】采用子图执行研究的一步，并且在状态中移除已经完成的步骤
    result = await researcher_graph.ainvoke({"question": state.steps[0]}, config=config)
    return {"documents": result["documents"], "steps": state.steps[1:]}

def check_finished(state: SuperviserState) -> Literal["respond", "conduct_research"]:
    """Determine if the research process is complete or if more research is needed.

    This function checks if there are any remaining steps in the research plan:
        - If there are, route back to the `conduct_research` node
        - Otherwise, route to the `respond` node

    Args:
        state (SuperviserState): The current state of the agent, including the remaining research steps.

    Returns:
        Literal["respond", "conduct_research"]: The next step to take based on whether research is complete.
    """
    # 检查是否还有未完成的研究步骤，没有的话继续执行，完成的话进行respond
    if len(state.steps or []) > 0:
        return "conduct_research"
    else:
        return "respond"

async def respond(
    state: SuperviserState, *, config: RunnableConfig
) -> dict[str, list[BaseMessage]]:
    """Generate a final response to the user's query based on the conducted research.

    This function formulates a comprehensive answer using the conversation history and the documents retrieved by the researcher.

    Args:
        state (SuperviserState): The current state of the agent, including retrieved documents and conversation history.
        config (RunnableConfig): Configuration with the model used to respond.

    Returns:
        dict[str, list[str]]: A dictionary with a 'messages' key containing the generated response.
    """
    configuration = ResearcherConfiguration.from_runnable_config(config)
    model = load_chat_model(configuration.response_model)
    context = format_docs(state.documents)
    prompt = configuration.response_system_prompt.format(context=context)
    messages = [{"role": "system", "content": prompt}] + state.messages
    response = await model.ainvoke(messages)
    return {"messages": [response]}


# Define the graph
builder = StateGraph(SuperviserState)
builder.add_node(create_research_plan)
builder.add_node(conduct_research)
builder.add_node(respond)
builder.add_edge(START, "create_research_plan")
builder.add_edge("create_research_plan", "conduct_research")
builder.add_conditional_edges(
    "conduct_research",
    check_finished,
    path_map={"respond": "respond", "conduct_research": "conduct_research"},
)
builder.add_edge("respond", END)
# Compile into a graph object that you can invoke and deploy.
graph = builder.compile()
graph.name = "ResearchAgent"
