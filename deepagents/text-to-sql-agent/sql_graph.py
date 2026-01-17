# 我们将使用 LangGraph 构建一个可以回答有关 SQL 数据库问题的自定义代理
import os
from langgraph.graph import StateGraph, MessagesState, START
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langgraph.prebuilt import ToolNode
from langchain_core.messages import AIMessage, HumanMessage
from langchain_community.utilities import SQLDatabase
from langchain.chat_models import init_chat_model

base_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(base_dir, "Chinook.db")

db = SQLDatabase.from_uri(
    # f"sqlite:///{db_path}"
    f"postgresql://postgres:postgres@localhost:5432/sqlbot"
)
model = init_chat_model(model="gpt-3.5-turbo")
# 3、为数据库添加工具
toolkit = SQLDatabaseToolkit(db=db, llm=model)
tools = toolkit.get_tools()


"""
sql_db_query: 此工具的输入是一个详细且正确的SQL查询，输出是来自数据库的结果。如果查询不正确，将返回错误消息。如果出现错误，请重写查询，检查查询并重试。如果遇到“Unknown column 'xxxx' in 'field list'”的问题，请使用sql_db_schema查询正确的表字段。
sql_db_schema: 此工具的输入是一个逗号分隔的表列表，输出是这些表的模式和示例行。请先使用sql_db_list_tables确认这些表确实存在！示例输入：table1, table2, table3
sql_db_list_tables: 输入为空字符串，输出是数据库中表的逗号分隔列表。
sql_db_query_checker: 在执行查询之前，使用此工具仔细检查您的查询是否正确。在使用sql_db_query执行查询之前，一定要使用此工具！
"""


# next:会返回生成器表达式找到的第一个匹配的对象。
get_schema_tool = next(tool for tool in tools if tool.name == "sql_db_schema")
# 获取相关表的模式
get_schema_node = ToolNode([get_schema_tool], name="get_schema")

run_query_tool = next(tool for tool in tools if tool.name == "sql_db_query")
# 执行SQL查询
run_query_node = ToolNode([run_query_tool], name="run_query")


# 1、列出数据库表
def list_tables(state: MessagesState):
    """List all tables in the database."""

    tool_call = {  # 预先设定一个工具的调用
        "name": "sql_db_list_tables",
        "args": {},
        "id": "abc123",
        "type": "tool_call",
    }
    tool_call_message = AIMessage(content="", tool_calls=[tool_call])

    list_tables_tool = next(tool for tool in tools if tool.name == "sql_db_list_tables")

    # 调用工具
    tool_message = list_tables_tool.invoke(tool_call)
    response = AIMessage(f"Available tables: {tool_message.content}")
    return {"messages": [tool_call_message, tool_message, response]}


def call_get_schema(state: MessagesState):
    """Get the schema of the specified tables."""

    # 获取

    # 调用工具
    tool_message = get_schema_tool.invoke(tool_call)
    response = AIMessage(f"Schema: {tool_message.content}")
    return {"messages": [tool_call_message, tool_message, response]}


# 2、获取工具

# 3、生成查询
# 4、检查查询


builder = StateGraph(MessagesState)

builder.add_node("list_tables", list_tables)

builder.add_edge(START, "list_tables")

graph = builder.compile()
