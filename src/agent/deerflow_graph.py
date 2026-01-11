
import logging

from langgraph.graph import START, END, StateGraph, MessagesState   

from agent.deerflow.types import State
from agent.deerflow.nodes import coordinator_node, background_investigation_node, planner_node


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
     handlers=[
        logging.StreamHandler()  # 将日志输出到控制台
    ]
)
logger = logging.getLogger(__name__)

builder = StateGraph(State)

builder.add_edge(START, 'coordinator')
builder.add_node('coordinator', coordinator_node)
builder.add_node("background_investigator", background_investigation_node)
builder.add_node("planner", planner_node)
builder.add_edge("background_investigator", "planner")
builder.add_edge('coordinator', END)
deerflow_graph = builder.compile()
