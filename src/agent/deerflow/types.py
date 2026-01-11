

from langgraph.graph.message import MessagesState

from agent.deerflow.prompts.planner_model import Plan


class State(MessagesState):
    locale: str = 'zh-CN' # 地区语言
    research_topic: str = '' # 研究主题
    clarification_rounds: int = 0 # 澄清轮次
    max_clarification_rounds: int = 3 # 最大澄清轮次
    enable_clarification: bool = True # 是否开启澄清
    goto: str = "planner"  # Default next node
    # 背景调查结果
    background_investigation_results: list = None
    plan_iterations: int = 0 # 计划迭代次数
    current_plan: Plan | str = None # 当前计划
