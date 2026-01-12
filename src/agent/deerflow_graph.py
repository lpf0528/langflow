
import logging

from agent.deerflow.graph.builder import build_deerflow_graph


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
     handlers=[
        logging.StreamHandler()  # 将日志输出到控制台
    ]
)
logger = logging.getLogger(__name__)



deerflow_graph = build_deerflow_graph()