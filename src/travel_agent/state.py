from pydantic import BaseModel, Field
import operator
from typing_extensions import TypedDict, Annotated, List, Sequence
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

# ===== STATE DEFINITIONS =====

class MapState(TypedDict):
    """
    State for the web search agent containing message history and research metadata.

    This state tracks the web search agent's conversation, iteration count for limiting
    tool calls, the research topic being investigated, compressed findings,
    and raw research notes for detailed analysis.
    """
    map_messages: Annotated[Sequence[BaseMessage], add_messages]
    tool_call_iterations: int
    map_result: str
    raw_notes: Annotated[List[str], operator.add]