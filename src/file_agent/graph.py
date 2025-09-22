from os import sync

from urllib3 import response
from file_agent.state import FileAgentState
from file_agent.configuration import FileAgentConfiguration

from langgraph.graph import END, START, StateGraph
from langchain_core.documents import Document
from langchain_core.messages import HumanMessage, SystemMessage, AIMessage
import os
from shared.utils import load_txt, load_pdf, load_word, format_docs, load_chat_model

async def read_file(state: FileAgentState) -> FileAgentState:
    """读取文件内容,将其转换为Document对象，注意，目前仅仅支持单个文件，且文件不能太长"""
    # print("STATE",state)
    # 读取最后一条消息
    if state.messages:
        last_message = state.messages[-1]
        file_path = last_message.additional_kwargs.get('file_path', None)
        if file_path:
            # 假设文件路径在消息内容中
            try:
                file_extension = os.path.splitext(file_path)[1].lower()
                if file_extension == '.txt':
                    file_ducuments = load_txt(file_path)
                elif file_extension == '.pdf':
                    file_documents = load_pdf(file_path)
                elif file_extension == '.docx' or file_extension == '.doc':
                    file_documents = load_word(file_path)
                else:
                    print(f"不支持的文件类型: {file_extension}")
                    file_documents = []
            except FileNotFoundError:
                print(f"文件未找到: {file_path}")
                file_documents = []
        else:
            file_documents = []
    return {"documents": file_documents}

async def llm_call(state: FileAgentState) -> FileAgentState:
    """读取文件内容,将其转换为Document对象"""
    # print("STATE",state)
    model = load_chat_model(FileAgentConfiguration().query_model)

    docs = format_docs(state.documents)

    content = state.messages[-1].content

    if len(content.strip()) == 0:
        content = "请对文件主要内容进行概述"

    messages = [
        SystemMessage(content=f"你是一个文件内容分析助手，根据文件内容回答问题。文件内容为{docs}"),
        *state.messages
    ]
    response = await model.ainvoke(messages)
    return {"messages": [response]}


builder = StateGraph(FileAgentState)
builder.add_node("read_file", read_file)
builder.add_node("llm_call", llm_call)
builder.add_edge(START, "read_file")
builder.add_edge("read_file", "llm_call")
builder.add_edge("llm_call", END)

"""
这里采用了工作流的形式来实现文件agent
注意：不加入短期记忆，每次都是单独的处理
注意：该agent与主agent的state共享messages字段和docunments字段
"""
graph = builder.compile()
graph.name = "FileAgentGraph"

