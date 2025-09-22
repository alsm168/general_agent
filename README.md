## 说明
# 基于LangGraph的通用对话多智能体


# 项目结构
- `src/`：项目的源代码目录
  - `superviser_graph/`：主图Superviser相关代码
  - `index_graph/`：用于基于字符串序列构建RAG索引相关代码
  - `retrieval_graph/`：检索langchain知识的RAG检索相关代码
  - `file_agent/`：用户给定输入文件（docx、pdf、text）问题图相关代码
  - `address_book_agent/`：地址簿excel问题图相关代码
  - `web_search_agent/`：网络搜索问题图相关代码
  - `travel_agent/`：基于百度地图MCP的旅行规划agent
  - `langchain_agent/`：Langchain实例的RAG问题图相关代码
  - `researcher_agent/`：Langgraph实例的RAG问题深入研究相关代码
  - `shared/`：共享代码，包括工具函数、模型加载等
  - `dev_function.py`：开发用的函数，用于测试和调试
- `certs/`：用于连接elastic的证书信息
- `tests/`：典型的测试用例，目前未覆盖所有测试
- `README.md`：项目的说明文档

# 主要功能
- 支持用户输入问题并生成响应
- 支持不同类型的问题，如基于excel的地址簿检索问题、基于文件问答问题、基于Web搜索的问答问题、基于MCP的旅行规划问题、基于RAG的langchain问答问、基于RAG的研究报告生成问题等
- 支持基于LangGraph的workflow、React Agent、Router构建的superviser多智能体架构

# 系统架构图

以下是superviser_agent的流程图，展示了整个系统的架构和各组件之间的关系：

```mermaid
---
config:
  flowchart:
    curve: linear
---
graph TD;
	__start__([<p>__start__</p>]):::first
	analyze_and_route_query(analyze_and_route_query)
	ask_for_more_info(ask_for_more_info)
	respond_to_general_query(respond_to_general_query)
	propose_action(propose_action)
	human_approval_node(human_approval_node)
	execute_action(execute_action)
	memory_node(memory_node)
	__end__([<p>__end__</p>]):::last
	__start__ --> analyze_and_route_query;
	address_book_agent_respond --> memory_node;
	analyze_and_route_query --> propose_action;
	conduct_travel_search_get_map_result --> memory_node;
	conduct_web_search_get_search_result --> memory_node;
	execute_action -.-> address_book_agent___start__;
	execute_action -.-> ask_for_more_info;
	execute_action -.-> conduct_travel_search___start__;
	execute_action -.-> conduct_web_search___start__;
	execute_action -.-> file_agent_read_file;
	execute_action -.-> researcher_agent_create_research_plan;
	execute_action -.-> respond_to_general_query;
	execute_action -.-> retrieval_agent_generate_query;
	file_agent_llm_call --> memory_node;
	human_approval_node -.-> execute_action;
	propose_action --> human_approval_node;
	researcher_agent_respond --> memory_node;
	retrieval_agent_respond --> memory_node;
	ask_for_more_info --> __end__;
	memory_node --> __end__;
	respond_to_general_query --> __end__;
	subgraph conduct_web_search
	conduct_web_search___start__(<p>__start__</p>)
	conduct_web_search_llm_call(llm_call)
	conduct_web_search_tool_node(tool_node)
	conduct_web_search_get_search_result(get_search_result)
	conduct_web_search___start__ --> conduct_web_search_llm_call;
	conduct_web_search_llm_call -.-> conduct_web_search_get_search_result;
	conduct_web_search_llm_call -.-> conduct_web_search_tool_node;
	conduct_web_search_tool_node --> conduct_web_search_llm_call;
	end
	subgraph conduct_travel_search
	conduct_travel_search___start__(<p>__start__</p>)
	conduct_travel_search_llm_call(llm_call)
	conduct_travel_search_tool_node(tool_node)
	conduct_travel_search_get_map_result(get_map_result)
	conduct_travel_search___start__ --> conduct_travel_search_llm_call;
	conduct_travel_search_llm_call -.-> conduct_travel_search_get_map_result;
	conduct_travel_search_llm_call -.-> conduct_travel_search_tool_node;
	conduct_travel_search_tool_node --> conduct_travel_search_llm_call;
	end
	subgraph retrieval_agent
	retrieval_agent_generate_query(generate_query)
	retrieval_agent_retrieve(retrieve)
	retrieval_agent_respond(respond)
	retrieval_agent_generate_query --> retrieval_agent_retrieve;
	retrieval_agent_retrieve --> retrieval_agent_respond;
	end
	subgraph researcher_agent
	researcher_agent_create_research_plan(create_research_plan)
	researcher_agent_respond(respond)
	researcher_agent_conduct_research_retrieve_documents -.-> researcher_agent_respond;
	researcher_agent_create_research_plan --> researcher_agent_conduct_research_generate_queries;
	subgraph conduct_research
	researcher_agent_conduct_research_generate_queries(generate_queries)
	researcher_agent_conduct_research_retrieve_documents(retrieve_documents)
	researcher_agent_conduct_research_retrieve_documents -.-> researcher_agent_conduct_research_generate_queries;
	researcher_agent_conduct_research_generate_queries -.-> researcher_agent_conduct_research_retrieve_documents;
	end
	end
	subgraph file_agent
	file_agent_read_file(read_file)
	file_agent_llm_call(llm_call)
	file_agent_read_file --> file_agent_llm_call;
	end
	subgraph address_book_agent
	address_book_agent___start__(<p>__start__</p>)
	address_book_agent_generate_query(generate_query)
	address_book_agent_retrieve(retrieve)
	address_book_agent_think(think)
	address_book_agent_respond(respond)
	address_book_agent___start__ --> address_book_agent_generate_query;
	address_book_agent_generate_query --> address_book_agent_retrieve;
	address_book_agent_retrieve --> address_book_agent_think;
	address_book_agent_think -.-> address_book_agent_generate_query;
	address_book_agent_think -.-> address_book_agent_respond;
	end
	classDef default fill:#f2f0ff,line-height:1.2
	classDef first fill-opacity:0
	classDef last fill:#bfb6fc
```

# 运行测试
```
python dev_function.py
```

# 贡献
欢迎提交Pull Request来改进项目。请确保在提交前运行测试并更新文档。

# 许可证
本项目基于MIT许可证开源。
