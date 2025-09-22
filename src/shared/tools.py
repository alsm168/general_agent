from langchain.tools import tool

@tool(parse_docstring=True)
def think_tool(reflection: str) -> str:
    """Tool for strategic reflection on research progress and decision-making.

    Use this tool after each search to analyze results and plan next steps systematically.
    This creates a deliberate pause in the research workflow for quality decision-making.

    When to use:
    - After receiving search results: What key information did I find?
    - Before deciding next steps: Do I have enough to answer comprehensively?
    - When assessing research gaps: What specific information am I still missing?
    - Before concluding research: Can I provide a complete answer now?

    Reflection should address:
    1. Analysis of current findings - What concrete information have I gathered?
    2. Gap assessment - What crucial information is still missing?
    3. Quality evaluation - Do I have sufficient evidence/examples for a good answer?
    4. Strategic decision - Should I continue searching or provide my answer?

    Args:
        reflection: Your detailed reflection on research progress, findings, gaps, and next steps

    Returns:
        Confirmation that reflection was recorded for decision-making
    """
    return f"Reflection: {reflection}"

"""
用于对研究进度和决策进行战略反思的工具。

在每次搜索后使用此工具，系统地分析搜索结果并规划下一步行动。
这会在研究工作流程中刻意停顿，以进行高质量的决策。

使用场景：
- 收到搜索结果后：我找到了哪些关键信息？
- 决定下一步行动前：我是否有足够的信息来给出全面的回答？
- 评估研究差距时：我还缺少哪些具体信息？
- 结束研究前：我现在能否给出完整的答案？

反思内容应涵盖：
1. 分析当前发现 - 我收集到了哪些具体信息？
2. 差距评估 - 我还缺少哪些关键信息？
3. 质量评估 - 我是否有足够的证据/示例来给出一个好的回答？
4. 战略决策 - 我应该继续搜索还是给出回答？

参数:
    reflection: 你对研究进度、发现、差距和下一步行动的详细反思

返回:
    确认反思内容已记录，用于决策制定
"""

