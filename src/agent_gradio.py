import gradio as gr
import asyncio
import uuid
from superviser_graph.graph import graph as main_agent

# 带 thread_id 的聊天函数
async def rag_react_stream_with_user_and_thread(message, history, user_id, session_state, web_search):
    # 检查是否已有thread_id，如果没有则生成新的
    if "thread_id" not in session_state:
        session_state["thread_id"] = str(uuid.uuid4())
    
    thread_id = session_state["thread_id"]
    
    print(f"user_id = {user_id}")
    print(f'thread_id={thread_id}')
    print(f'message={message}')
    print(f'web_search={web_search}')
    config = {"configurable": {"thread_id": thread_id, "user_id": user_id}}

    # 先 yield 一个"稍等"提示
    yield "请稍等，我正在处理您的问题..."

    response = ""
    interrupted = False
    interrupt_content = ''
    async for chunk in main_agent.astream({"messages": [{"role": "user", "content": message}],
    "choose_web_search": web_search}, config, stream_mode=["messages", "updates"]):
        # 跳过工具输出
        if chunk[0] == 'messages':
            message, meta_data = chunk[1]
            if meta_data.get('langgraph_node') == 'tools':
                continue
            if meta_data.get('langgraph_node') == 'analyze_and_route_query':\
                continue
            if message.content:
                response += message.content
                yield response
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
    if interrupted:
        # response += f'中断原因：{interrupt_content}'
        print("检测到中断，需要人工审核")
        # 模拟人工审核（在实际应用中，这里应该是一个用户界面）
        approval = input(f"{interrupt_content}\n\n批准操作吗？(yes/no): ")
        if approval.lower() == 'yes':
            approval = 'approve'
            try:
                async for chunk in main_agent.astream(Command(resume={"user_response": approval}),
                    stream_mode=['messages', 'updates'],
                    config=config,
                    ):
                    if chunk[0] == 'messages':
                        message, meta_data = chunk[1]
                        if meta_data.get('langgraph_node') == 'tools':
                            continue
                        if meta_data.get('langgraph_node') == 'analyze_and_route_query':\
                            continue
                        if message.content:
                            response += message.content
                            yield response
            except Exception as e:
                print(f"修订执行过程中发生错误: {e}")

# 自动填充示例聊天内容
def prefill_chatbot(choice):
    if choice == "Greeting":
        return [
            {"role": "user", "content": "Hi there!"},
            {"role": "assistant", "content": "Hello! How can I assist you today?"}
        ]
    elif choice == "Complaint":
        return [
            {"role": "user", "content": "I'm not happy with the service."},
            {"role": "assistant", "content": "I'm sorry to hear that. Can you please tell me more about the issue?"}
        ]
    else:
        return []

# 主 Gradio 界面构建
with gr.Blocks() as demo_block:
    # 创建会话状态
    session_state = gr.State({})
    
    # with gr.Column():
    #     radio = gr.Radio(["Greeting", "Complaint", "Blank"], label="选择预设对话")
    with gr.Column():  # 按列进行排列
        chat = gr.ChatInterface(
            fn=rag_react_stream_with_user_and_thread,
            type="messages",
            additional_inputs=[
                gr.Textbox(placeholder="请输入您的 user_id", label="User ID"),
                session_state,
                gr.Checkbox(label="启用网络搜索", value=False)],
            chatbot=gr.Chatbot(height=300, type="messages"),  # ← 修复这里
            textbox=gr.Textbox(placeholder="请输入你的问题", container=False, ),
            title="通用对话机器人",
            description="我是通用对话的智能体，帮你旅行规划、网络检索",
            theme="ocean",
        )

        # 添加清空对话按钮
        clear_btn = gr.Button("清空对话")

        # 点击按钮时，清空 chatbot 内容并重置会话状态
        def clear_chat_and_session():
            return None, {}, False
        
        clear_btn.click(clear_chat_and_session, outputs=[chat.chatbot, session_state, chat.additional_inputs[2]])
    # radio.change(prefill_chatbot, inputs=radio, outputs=chat)

# 启动 Gradio，无参数 queue()
# http://192.168.1.2:7860/
demo_block.queue().launch(server_name="0.0.0.0", server_port=7860, share=True)

