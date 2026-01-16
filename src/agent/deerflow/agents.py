from agent.deerflow.config.agents import AGENT_LLM_MAP


def create_agent(agent_name, agent_type):
    llm = AGENT_LLM_MAP.get(agent_type, "basic")
