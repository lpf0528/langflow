

from langgraph.graph import START, END, StateGraph
from langgraph.types import Checkpointer   
from agent.deerflow.types import State
from agent.deerflow.nodes import coordinator_node, background_investigation_node, planner_node


def _build_base_deerflow_graph() -> StateGraph:
    builder = StateGraph(State)
    builder.add_edge(START, 'coordinator')
    builder.add_node('coordinator', coordinator_node)
    builder.add_node("background_investigator", background_investigation_node)
    builder.add_node("planner", planner_node)
    # builder.add_node("human_feedback", human_feedback_node)
    builder.add_edge("background_investigator", "planner")
    builder.add_edge('coordinator', END)
    return builder

def build_deerflow_graph(checkpointer: Checkpointer = None) -> StateGraph:
    builder = _build_base_deerflow_graph()
    return builder.compile(checkpointer=checkpointer)
