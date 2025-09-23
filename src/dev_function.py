from langchain_core.messages import HumanMessage

# 测试file_agent,这里采用了工作流的形式来实现文件agent
import asyncio
from file_agent.graph import graph as file_agent_graph
from address_book_agent.graph import graph as address_book_agent_graph
from web_search_agent.graph import graph as web_search_agent_graph
from researcher_agent.graph import graph as researcher_agent_graph

from superviser_graph import graph as main_agent
from retrieval_graph.graph import graph as retrieval_agent
from travel_agent.graph import graph as travel_agent


from dotenv import load_dotenv, find_dotenv
_ = load_dotenv(find_dotenv())


def dev_messgae():
    message = HumanMessage(content="分析文件", file_path="s3://bucket/key.pdf", data='mine')
    print(message)



def dev_file_agent():
    """用来测试file_agent"""
    result = asyncio.run(file_agent_graph.ainvoke({"messages": [{
        "role": "user",
        "content": "看守所关于个人权利有哪些规定", 
        "file_path": "/mnt/sdb/lsm/work/data/paper/中华人民共和国看守所条例实施办法.docx"}]}))
    print(result["messages"][-1].content)

async def dev_main_agent():
    """用来测试main_agent"""
    config = {
        "configurable": {
            'thread_id': 'lsm'
        }
    }
    use_values = True
    if use_values:
        async for chunk in main_agent.astream({"messages": [{
            "role": "user",
            "content": "看守所关于个人权利有哪些规定", 
            "file_path": "/mnt/sdb/lsm/work/data/paper/中华人民共和国看守所条例实施办法.docx"}]},
            stream_mode='values',
            config=config,
            ):
            print(chunk)
        
        print("*"*30)
        async for chunk in main_agent.astream({"messages": [{
            "role": "user",
            "content": "周博文的手机和邮箱是什么"}]},
            stream_mode='values',
            config=config,
            ):
            print(chunk)
    else:
        async for chunk, chunk_infor  in main_agent.astream({"messages": [{
            "role": "user",
            "content": "看守所关于个人权利有哪些规定", 
            "file_path": "/mnt/sdb/lsm/work/data/paper/中华人民共和国看守所条例实施办法.docx"}]},
            stream_mode='messages',
            config=config,
            ):
            print(chunk.content)
        
        print("*"*30)
        async for chunk, chunk_infor in main_agent.astream({"messages": [{
            "role": "user",
            "content": "上述文件关于生活卫生的有哪些规定"}]},
            stream_mode='messages',
            config=config,
            ):
            print(chunk.content)


async def dev_address_book_agent():
    """用来测试address_book_agent"""
    async for chunk in address_book_agent_graph.astream({"messages": [{
        "role": "user",
        "content": "张三的电话和邮箱是什么"}]},
        stream_mode='values',
        ):
        print(chunk)

async def dev_web_search_agent():
    """用来测试web_search_agent"""
    async for chunk in web_search_agent_graph.astream({"web_search_messages": [{
        "role": "user",
        "content": "怎么做饺子"}]},
        stream_mode='values',
        ):
        print(chunk)

async def dev_web_search_agent_with_main():
    """用来测试web_search_agent"""
    config = {
        "configurable": {
            'thread_id': 'lsm'
        }
    }
    async for chunk in main_agent.astream({"messages": [{
        "role": "user",
        "content": "怎么做电脑"}],"choose_web_search": True},
        stream_mode='values',
        config=config,
        ):
        print(chunk)

async def make_vector_store():
    """构建自定义的向量数据库"""
    from index_graph import graph as index_graph
    config = {
        "configurable": {
            'thread_id': 'lsm',
            'index_name': 'home_doing_index',
        }
    }
    x = await index_graph.ainvoke({"docs": ['小明在家里做了一个机器人', '小李在家里写作业']}, config=config)
    return x

async def make_vector_store_2():
    """构建默认的向量数据库-是一个langchain的数据库"""
    from index_graph import graph as index_graph
    config = {
        "configurable": {
            'thread_id': 'lsm',
            'index_name': 'langchain_book_index',
        }
    }
    x = await index_graph.ainvoke({"docs": []}, config=config)
    return x

async def dev_elastic_retriever():
    from shared.retrieval import make_elastic_retriever, make_text_encoder
    from shared.configuration import BaseConfiguration
    from langchain_core.embeddings import Embeddings
    from langchain_core.vectorstores import VectorStoreRetriever

    config = BaseConfiguration()
    config.index_name = "home_doing_index"
    embedding_model = make_text_encoder(config.embedding_model)
    with make_elastic_retriever(config, embedding_model) as retriever:
        response = retriever.invoke("小明在家里做什么")
        print(response)
    
async def dev_retrieval_agent():
    """用来测试retrieval_agent"""
    config = {
        "configurable": {
            'thread_id': '12345',
            'user_name': 'lsm',
            'index_name': 'langchain_book_index',
        }
    }
    async for chunk in retrieval_agent.astream({"messages": [{
        "role": "user",
        "content": "langchain有哪些特点"}]},
        stream_mode='values',
        config=config,
        ):
        print(chunk)


async def dev_retrieval_agent_with_main():
    """用来测试retrieval_agent"""
    config = {
        "configurable": {
            'thread_id': '12345',
            'user_name': 'lsm',
            'index_name': 'langchain_book_index',
        }
    }
    async for chunk in main_agent.astream({"messages": [{
        "role": "user",
        "content": "langchain有哪些特点"}]},
        stream_mode='values',
        config=config,
        ):
        print(chunk)
        
import uuid
async def dev_retrieval_agent_with_main_for_audit():
    """
    用来测试 retrieval_agent
    注意：只有updatesm模式下才会检测中断！！！！！！！！！！！！！！！！！！！！！！！！！！
    所以只有采用【messages、updates】组合模式下才能处理好interrupt问题
    """
    from langgraph.types import Command
    """用来测试retrieval_agent"""
    config = {
        "configurable": {
            'thread_id': uuid.uuid4(),
            'user_name': 'lsm',
            'index_name': 'langchain_book_index',
        }
    }
    
    # 使用流式处理来检测中断
    print("开始执行检索代理...")
    interrupted = False
    
    try:
        async for chunk in main_agent.astream({"messages": [{
            "role": "user",
            # "content": "我是研发工程师，请问langchain有哪些特点"}]},
            "content": "帮我规划明天从海淀到环球影城的旅游计划"}]},
            stream_mode='updates',
            config=config,
            ):
            print("当前更新:")
            print(chunk)
            
            # 检查是否包含中断相关的信息
            if isinstance(chunk, dict):
                # 检查是否有任何节点被中断
                for key, value in chunk.items():
                    if key == "__interrupt__":
                        print(f"检测到中断: {value}")
                        interrupted = True
                        break
                
                if interrupted:
                    break
    except Exception as e:
        print(f"执行过程中发生错误: {e}")
        interrupted = True
    
    if interrupted:
        print("检测到中断，需要人工审核")
        
        # 模拟人工审核（在实际应用中，这里应该是一个用户界面）
        approval = input("批准操作吗？(yes/no): ")
        
        if approval.lower() == 'yes':
            approval = 'approve'
            try:
                async for chunk in main_agent.astream(Command(resume={"user_response": approval}),
                    stream_mode='updates',
                    config=config,
                    ):
                    print("当前修订:")
                    print(chunk)
            except Exception as e:
                print(f"修订执行过程中发生错误: {e}")
        else:
            approval = 'reject'
            user_type = input("请选择分类(file_question, address_book, more-info, langchain, general, web_search, langgraph): ")
            try:
                async for chunk in main_agent.astream(Command(resume={"user_response": approval, "type": user_type}),
                    stream_mode='updates',
                    config=config,
                    ):
                    print("当前修订:")
                    print(chunk)
            except Exception as e:
                print(f"修订执行过程中发生错误: {e}")


async def dev_retrieval_agent_with_main_for_auditv2():
    from langgraph.types import Command
    from langgraph.errors import NodeInterrupt  # 注意 import 正确的异常类
    """用来测试retrieval_agent"""
    config = {
        "configurable": {
            'thread_id': uuid.uuid4(),
            'user_name': 'lsm',
            'index_name': 'langchain_book_index',
        }
    }
    
    # 使用流式处理来检测中断
    print("开始执行检索代理...")
    interrupted = False
    interrupt_content = ''
    
    try:
        async for chunk in main_agent.astream({"messages": [{
            "role": "user",
            # "content": "我是研发工程师，请问langchain有哪些特点"}]},
            "content": "帮我规划明天从海淀到环球影城的旅游计划"}]},
            stream_mode=['updates', 'messages'],
            config=config,
            ):
            if chunk[0] == 'messages':
                message, meta_data = chunk[1]
                if meta_data.get('langgraph_node') == 'tools':
                    continue
                if meta_data.get('langgraph_node') == 'analyze_and_route_query':\
                    continue
                if message.content:
                    print(message.content, end='', flush=True)
            elif chunk[0] == 'updates':
                # 检查是否包含中断相关的信息
                chunk_sub = chunk[1]
                if isinstance(chunk_sub, dict):
                    # 检查是否有任何节点被中断
                    for key, value in chunk_sub.items():
                        if key == "__interrupt__":
                            # print(f"检测到interrupt中断: {value}")
                            interrupt_content = value[0].value['question']
                            interrupted = True
                            break
                    
                    if interrupted:
                        break
        print('\n')
    except Exception as e:
        print(f"执行过程中发生错误: {e}")
        interrupted = True
    print(f"interrupted={interrupted}|interrupt_content={interrupt_content}--------------------------------------------------")
    
    if interrupted:
        print("检测到中断，需要人工审核")
        
        # 模拟人工审核（在实际应用中，这里应该是一个用户界面）
        approval = input("批准操作吗？(yes/no): ")
        
        if approval.lower() == 'yes':
            approval = 'approve'
            try:
                async for chunk in main_agent.astream(Command(resume={"user_response": approval}),
                    stream_mode='updates',
                    config=config,
                    ):
                    print("当前修订:")
                    print(chunk)
            except Exception as e:
                print(f"修订执行过程中发生错误: {e}")
        else:
            approval = 'reject'
            user_type = input("请选择分类(file_question, address_book, more-info, langchain, general, web_search, langgraph): ")
            try:
                async for chunk in main_agent.astream(Command(resume={"user_response": approval, "type": user_type}),
                    stream_mode='updates',
                    config=config,
                    ):
                    print("当前修订:")
                    print(chunk)
            except Exception as e:
                print(f"修订执行过程中发生错误: {e}")


async def dev_researcher_agent():
    """用来测试researcher_agent"""
    config = {
        "configurable": {
            'thread_id': '12345',
            'user_name': 'lsm',
            'index_name': 'langchain_book_index',
        }
    }
    async for chunk in researcher_agent_graph.astream({"messages": [{
        "role": "user",
        "content": "langchain在构建RAG过程中有哪些注意事项"}]},
        stream_mode='values',
        config=config,
        ):
        print(chunk)
    

async def dev_map_agent():
    """用来测试map_agent"""
    config = {
        "configurable": {
            'thread_id': '12345',
            'user_name': 'lsm',
        }
    }
    async for chunk in travel_agent.astream({"map_messages": [{
        "role": "user",
        "content": "帮我规划明天从海淀到环球影城的旅游计划"}]},
        stream_mode='values',
        config=config,
        ):
        print(chunk)



if __name__ == "__main__":
    """用来测试主agent和子agent，整体采用Router架构，子图采用工作流或react_agent架构"""
    do_it = 6
    if do_it == 1:
        asyncio.run(dev_main_agent())
    if do_it == 2:
        asyncio.run(dev_address_book_agent())

    if do_it == 3:
        asyncio.run(dev_web_search_agent_with_main())
    if do_it == 4:
        # vectorstore = asyncio.run(make_vector_store())
        vectorstore = asyncio.run(make_vector_store_2())
    if do_it == 5:
        asyncio.run(dev_elastic_retriever())
    if do_it == 6:
        # asyncio.run(dev_retrieval_agent())
        asyncio.run(dev_retrieval_agent_with_main_for_auditv2())
    if do_it == 7:
        asyncio.run(dev_researcher_agent())
    if do_it == 8:
        asyncio.run(dev_map_agent())

