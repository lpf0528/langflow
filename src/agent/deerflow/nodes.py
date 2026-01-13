
import json
import logging

import re
from typing import Literal
from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.runnables.config import RunnableConfig
from langgraph.types import Command, interrupt
from agent.deerflow.config.agents import AGENT_LLM_MAP
from agent.deerflow.config.configuration import Configuration
from agent.deerflow.llms.llm import get_llm_by_type
from agent.deerflow.prompts import apply_prompt_template
from agent.deerflow.prompts.planner_model import Plan
from agent.deerflow.tools.search import LoggedTavilySearch
from agent.deerflow.types import State
from agent.deerflow.config.tools import SELECTED_SEARCH_ENGINE, SearchEngine
from agent.deerflow.node_tools import handoff_after_clarification, handoff_to_planner, direct_response
from agent.deerflow.utils import build_clarified_topic_from_history, get_message_content, reconstruct_clarification_history

logger = logging.getLogger(__name__)


def coordinator_node(
    state: State, config: RunnableConfig
)->Command[Literal['__end__']]:
    """
    Coordinator node
    """
    logger.info(f'协调器节点 is running.{config}')
    messages = apply_prompt_template('coordinator', state)
    enable_clarification = state.get('enable_clarification', False)
    clarified_topic = None
    research_topic = state.get('research_topic', '')
    if not enable_clarification:
        # 关闭澄清
        messages.append({
            "role": "system", 
            "content": "澄清功能已禁用。对于研究问题,使用 handoff_to_planner。对于问候或闲聊,使用 direct_response。不要提出澄清问题。",
        })
        tools = [handoff_to_planner, direct_response]
        response = (
            get_llm_by_type(AGENT_LLM_MAP["coordinator"])
            .bind_tools(tools)
            .invoke(messages)
        )
        goto = '__end__'
        # if response.tool_calls:
        #     # 存在工具调用
        #     for tool_call in response.tool_calls:
        #         tool_name = tool_call.get('name', '')
        #         tool_args = tool_call.get('args', {})

        #         if tool_name == 'handoff_to_planner':
        #             goto = 'planner'
        #             research_topic = tool_args.get('research_topic', '')
        #             break

        #         elif tool_name == 'direct_response':
        #             goto = '__end__'
        #             message = tool_args.get('message', '')
        #             if message:
        #                 messages.append(AIMessage(content=message, name='coordinator'))
        #             break
    else:
        # 开启澄清
        clarification_rounds = state.get('clarification_rounds', 0)
        max_clarification_rounds = state.get('max_clarification_rounds', 3)

        if clarification_rounds == 0:
            # 首次澄清
            messages.append({
                "role": "user", 
                "content": '澄清模式已启用。请遵循你指令中的"澄清流程"指南。',
            })
        # 澄清历史(用户的消息)
        state_messages = list(state.get('messages', []))
        clarification_history = reconstruct_clarification_history(state_messages)
        clarified_topic = build_clarified_topic_from_history(clarification_history)
        current_response = clarification_history[-1] if clarification_history else "No response"

        # 构建澄清上下文
        clarification_context = f"""继续澄清(第{clarification_rounds}轮/共{max_clarification_rounds}轮):
            用户最新回复: {current_response}。
            请询问仍然缺失的维度。不要重复已问过的问题或开始新话题。
        """
        messages.append({
            "role": "system", 
            "content": clarification_context,
        })
        
        if clarification_rounds >= max_clarification_rounds:
            # 达到最大澄清轮次
            messages.append({
                "role": "system", 
                "content": f"已达到最大轮数。你必须调用 handoff_after_clarification(而不是 handoff_to_planner),根据用户的语言使用适当的语言环境,并设置 research_topic='{clarified_topic}'。不要再提出任何问题。",
            })

        tools =[handoff_to_planner, handoff_after_clarification]
        response = (
            get_llm_by_type(AGENT_LLM_MAP["coordinator"])
            .bind_tools(tools)
            .invoke(messages)
        )
        goto = '__end__'

        if not response.tool_calls and response.content:
            # 没有工具调用，直接回复用户

            clarification_rounds += 1 # 澄清次数+1
            updated_messages = list(state_messages)
            updated_messages.append(HumanMessage(content=response.content, name='coordinator'))

            return Command(update={
                'messages': updated_messages,
                'clarification_rounds': clarification_rounds,
            }, goto=goto)

    # 存在工具的调用
    if response.tool_calls:
        for tool_call in response.tool_calls:
            tool_name = tool_call.get('name','')
            tool_args = tool_call.get('args', {})
            # 工具：移交给规划者或者澄清后移交
            if tool_name in ('handoff_to_planner', 'handoff_after_clarification'):
                goto = 'planner'
                if tool_args.get('research_topic'):
                    research_topic = tool_args.get('research_topic')
                break
    # 去往规划器前，是否开启背景调查
    if goto == 'planner' and  state.get('enable_background_investigation'):
        goto = 'background_investigator'

    research_topic = clarified_topic or research_topic
    return Command(update={
        'messages': messages,
        'research_topic':research_topic,
        'goto': goto,
    }, goto=goto)


def background_investigation_node(state: State, config: RunnableConfig):
    logger.info('背景调查节点 is running.')
    # 是否开启web搜索
    configuration = Configuration.from_runnable_config(config)
    if not configuration.enable_web_search:
        logger.info('背景调查节点 未开启web搜索')
        return {
            'background_investigation_results':json.dumps([], ensure_ascii=False)
        }
    # 搜索的话题
    query = state.get('research_topic', '')
    background_investigation_results = []
    # 搜索引擎
    if SELECTED_SEARCH_ENGINE == SearchEngine.TAVILY.value:
        searched_content = LoggedTavilySearch(max_results=configuration.max_search_results).invoke(query)
        if isinstance(searched_content, tuple):
            searched_content = searched_content[0]
        if isinstance(searched_content, str):
            try:
                parsed = json.loads(searched_content)
                if isinstance(parsed, dict):
                    logger.error(f'背景调查节点 解析搜索结果解析失败: {parsed}')
                if isinstance(searched_content, list):
                    background_investigation_results = [
                        f'## {elem.get("title", "Untitled")}\n{elem.get("content")}'
                        for elem in parsed if elem.get('content', None)
                    ]
            except json.JSONDecodeError:
                logger.error(f'背景调查节点 解析搜索结果解析失败: {searched_content}')
        elif isinstance(searched_content, list):
            background_investigation_results = [
                f'## {elem.get("title", "Untitled")}\n{elem.get("content")}'
                for elem in searched_content if elem.get('content', None)
            ]
    else:
        # 其他搜索引擎
        pass
    return {
        'background_investigation_results':json.dumps(background_investigation_results, ensure_ascii=False)
    }

def planner_node(state: State, config: RunnableConfig):
    # 规划器
    logger.info('规划器节点 is running.')
    
    configuration = Configuration.from_runnable_config(config)

    # 1、用户的话题
    modified_state = state.copy()
    modified_state['messages'] = [
        {'role':'user', 'content':state['research_topic']}
    ]
    messages = apply_prompt_template('planner', modified_state, config)
    # 2、是否开启背景调查
    if state.get('enable_background_investigation'):
        messages +=[
            {'role':'user', 'content':f"""
            用户话题背景调查的结果：
            {state.get('background_investigation_results', '')}
            """
            }
        ]

    # 3、计划迭代次数 >= 最大迭代次数 ——> 生成报告
    if state.get('plan_iterations', 0) >= configuration.max_plan_iterations:
        return Command(goto='reporter')

    # 4、开启规划
    llm = get_llm_by_type(AGENT_LLM_MAP["planner"])
    response = llm.invoke(messages)
    if hasattr(response, 'model_dump_json'):
        # exclude_none：这个参数指定在导出 JSON 时应排除值为 None 的字段
        full_response = response.model_dump_json(indent=4, exclude_none=True)
    else:
        full_response = get_message_content(response) or ''
    
    logger.info(f'规划器节点 回复: {full_response}')

    curr_plan = json.loads(full_response)
    # 5、处理规划内容
    curr_plan = json.loads(curr_plan.get('content', '{}'))
    new_plan = Plan.model_validate(curr_plan)
    # 是否有足够的上下文
    if isinstance(curr_plan, dict) and curr_plan.get('has_enough_context'):
        # 6、有足够的上下文，生成报告
        return Command(update={
            'messages':[AIMessage(content=full_response, name='planner')],
            'current_plan': new_plan
        }, goto='reporter')
    # 7、没有足够的上下文，等待用户反馈
    return Command(update={
        "messages": [AIMessage(content=full_response, name="planner")],
        "current_plan": new_plan,
    }, goto='human_feedback')



def human_feedback_node(state: State, config: RunnableConfig):
    # 1、是否自动接受计划
    if not state.get('auto_accepted_plan', False):
        # 不自动接收：等待用户反馈
        user_feedback = interrupt('Please Review the Plan.')
        if not user_feedback:
            # 没有用户反馈，返回计划节点生成新的计划
            # TODO:提取在状态转换中应该保留的元数据/配置字段。
            return Command(goto='planner')
        user_feedback = str(user_feedback).strip().upper()

        # 是否接受计划
        if user_feedback.startswith('[EDIT_PLAN]'):
            # 不接受计划，返回计划节点
            return Command(update={
                'messages':[
                    HumanMessage(content=user_feedback, name='feedback')
                ]
            },goto='planner')
        elif user_feedback.startswith('[ACCEPTED]'):
            # 接受计划，直接执行
            pass
        else:
            # 未知行为：重回计划节点
            return Command(goto='planner')
    goto = "research_team"
    # 接收计划
    plan_iterations = state.get('plan_iterations', 0)
    plan_iterations += 1
    return Command(update={
        'plan_iterations':plan_iterations,
    }, goto=goto)
    

        

    # 否：人在环中：接收用户反馈

    # -- 没有反馈：去向计划节点
    # -- 编辑计划：加上用户反馈 -> 计划节点
    
    # 接受计划：直接执行



    