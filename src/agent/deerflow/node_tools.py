from typing import Annotated
from langchain_core.tools import tool
@tool
def handoff_to_planner(
    research_topic: Annotated[str, "移交的研究任务的主题"],
    locale: Annotated[str, "用户检测到的语言区域 (e.g., en-US, zh-CN)."],
):
    """将任务移交给规划代理执行"""
    # 这个工具不返回任何内容：仅使用它作为让大语言模型发出移交给规划代理的信号。
    return


@tool
def direct_response(
    locale: Annotated[str, "用户检测到的语言区域 (e.g., en-US, zh-CN)."],
    message: Annotated[str, "直接发送给用户的结束回复消息。"],
):
    """直接回复用户的问候、闲聊或礼貌拒绝。不要将此用于研究问题 - 应使用 handoff_to_planner 代替。"""
    return

@tool
def handoff_after_clarification(
    research_topic: Annotated[str, "基于所有澄清步骤的明确研究主题。"],
    locale: Annotated[str, "用户检测到的语言区域 (e.g., en-US, zh-CN)."]
):
    """澄清轮次完成后移交给规划者，将所有的澄清历史传递给规划者进行分析。"""
    return
