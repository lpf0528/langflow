from langgraph.graph import START, END, StateGraph
from langgraph.types import Checkpointer
from agent.deerflow.types import State
from agent.deerflow.nodes import (
    coordinator_node,
    background_investigation_node,
    planner_node,
    human_feedback_node,
    research_team_node,
)


def continue_to_running_research_team(state: State):

    return "planner"


def _build_base_deerflow_graph() -> StateGraph:
    builder = StateGraph(State)
    builder.add_edge(START, "coordinator")
    builder.add_node("coordinator", coordinator_node)
    builder.add_node("background_investigator", background_investigation_node)
    builder.add_node("planner", planner_node)
    builder.add_node("human_feedback", human_feedback_node)
    builder.add_node("research_team", research_team_node)
    builder.add_conditional_edges(
        "research_team",
        continue_to_running_research_team,
        ["planner", "researcher", "analyst", "coder"],
    )
    builder.add_edge("background_investigator", "planner")

    builder.add_edge("coordinator", END)
    return builder


def build_deerflow_graph(checkpointer: Checkpointer = None) -> StateGraph:
    builder = _build_base_deerflow_graph()
    return builder.compile(checkpointer=checkpointer)
