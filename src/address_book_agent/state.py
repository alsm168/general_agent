from dataclasses import dataclass, field
from typing import Annotated, Any, Literal, Optional, Sequence, Union

from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages
from operator import add
from pydantic import BaseModel, Field

#############################  Agent State  ###################################


def add_queries(existing: Sequence[str], new: Sequence[str]) -> Sequence[str]:
    """Combine existing queries with new queries.

    Args:
        existing (Sequence[str]): The current list of queries in the state.
        new (Sequence[str]): The new queries to be added.

    Returns:
        Sequence[str]: A new list containing all queries from both input sequences.
    """
    return list(existing) + list(new)

class SearchQuery(BaseModel):
    """Search the indexed documents for a query."""

    query: str = Field(description="Search query")

class ThinkContent(BaseModel):
    """Schema for think content."""
    need_retrive: bool = Field(
        description="Whether the agent needs to retrive the user query.",
    )
    thought: str = Field(
        description="Thought that the agent has about the current state.",
    )

@dataclass(kw_only=True)
class State:
    """The state of your graph / agent."""
    messages: Annotated[Sequence[AnyMessage], add_messages]

    queries: Annotated[list[str], add_queries] = field(default_factory=list)
    """A list of search queries that the agent has generated."""

    retrieved_books: Annotated[list[str], add_queries] = field(default_factory=list)
    """检索到的通讯录信息"""

    think_count: Annotated[int, add] = field(
        default=0,
        metadata={
            "description": "The number of times the agent has thought about the current state."
        },
    )

    think_content: Optional[ThinkContent] = None

    # Feel free to add additional attributes to your state as needed.
    # Common examples include retrieved documents, extracted entities, API connections, etc.


