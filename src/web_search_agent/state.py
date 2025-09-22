from pydantic import BaseModel, Field
import operator
from typing_extensions import TypedDict, Annotated, List, Sequence
from pydantic import BaseModel, Field
from langchain_core.messages import BaseMessage
from langgraph.graph.message import add_messages

# ===== STATE DEFINITIONS =====

class WebSearchState(TypedDict):
    """
    用于网络搜索代理的状态，包含消息历史记录和研究元数据。

    此状态跟踪网络搜索代理的对话、用于限制工具调用的迭代次数、正在研究的主题、压缩后的研究结果，
    以及用于详细分析的原始研究笔记。
    """
    web_search_messages: Annotated[Sequence[BaseMessage], add_messages]
    tool_call_iterations: int
    web_search_result: str
    raw_notes: Annotated[List[str], operator.add]


class Summary(BaseModel):
    """Schema for webpage content summarization."""
    summary: str = Field(description="Concise summary of the webpage content")
    key_excerpts: str = Field(description="Important quotes and excerpts from the content")