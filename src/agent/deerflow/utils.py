

from typing import Any

from click.formatting import measure_table
from langchain_core.messages import HumanMessage

ASSISTANT_SPEAKER_NAMES = {
    "coordinator",
    "planner",
    "researcher",
    "coder",
    "reporter",
    "background_investigator",
}

def build_clarified_topic_from_history(clarification_history: list[str]):
    sequence = [item for item in clarification_history if item]
    if not sequence:
        return ''
    if len(sequence) == 1:
        return sequence[0]
    head, *tail = sequence
    clarified_str = f'{head}- {",".join(tail)}'
    return clarified_str



def reconstruct_clarification_history(messages:list[Any]):
    """
    从消息列表中提取用户澄消息
    """
    sequence: list[str] = []

    for message in messages:
        if not is_user_message(message):
            # 不是用户消息
            continue
        content = get_message_content(message)
        if not content:
            continue
        if sequence and sequence[-1] == content:
            # 如果当前消息和上一条消息相同，则忽略
            continue
        sequence.append(content)

    if sequence:
        return sequence
    return []
    


def get_message_content(message: Any)->str:
    if isinstance(message, dict):
        return message.get('content', '')
    return getattr(message, 'content', '')


def is_user_message(message: Any) -> bool:

    if isinstance(message, HumanMessage):
        message_type = (getattr(message, 'type', '') or '').lower()
        name = (getattr(message, 'name', '') or '').lower() # 用户输入的消息没有name
        if message_type == 'human':
            # 有名字的消息，且名字在ASSISTANT_SPEAKER_NAMES中，都不是用户消息，是node中定义的消息
            return not (name and name in ASSISTANT_SPEAKER_NAMES)
    return False