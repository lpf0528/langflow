
import os
from langchain_core.runnables import RunnableConfig
from langchain.agents import AgentState
from datetime import datetime
from jinja2 import Environment, FileSystemLoader, TemplateNotFound, select_autoescape

env = Environment(
    loader=FileSystemLoader(os.path.dirname(__file__)),
    autoescape=select_autoescape(),
    trim_blocks=True,
    lstrip_blocks=True,
)


def apply_prompt_template(
    prompt_template: str,
    state: AgentState,
    config: RunnableConfig = None,
    locale: str = "zh-CN"
) -> str:
    """
    Apply prompt template
    """
    state_vars = {  
         'CURRENT_TIME': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        **state
    }
    if config:
        state_vars.update(config)
    
    try:
        template = env.get_template(f'{prompt_template}.md')
    except TemplateNotFound:
        raise ValueError(f"Invalid prompt template: {prompt_template}")
    system_prompt = template.render(**state_vars)
    return [{"role": "system", "content": system_prompt}] + state["messages"]
