import os
from typing import Literal
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain.chat_models import init_chat_model
from langgraph.prebuilt import ToolNode
from langchain.messages import AIMessage
from langgraph.graph import END, START, MessagesState, StateGraph
from langchain_core.runnables import RunnableConfig
from langchain_core.tools import tool
from langgraph.types import interrupt
from langgraph.checkpoint.memory import InMemorySaver

base_dir = os.path.dirname(os.path.abspath(__file__))
db_path = os.path.join(base_dir, "chinook.db")
# 1、配置数据库
db = SQLDatabase.from_uri(
    "postgresql://postgres:postgres@localhost:5432/sqlbot",
    # f"sqlite:///{db_path}",
    # sample_rows_in_table_info=3,
)
model = init_chat_model("gpt-4o-mini")

toolkit = SQLDatabaseToolkit(db=db, llm=model)
tools = toolkit.get_tools()
# 获取数据库表结构
get_schema_tool = next(tool for tool in tools if tool.name == "sql_db_schema")
get_schema_node = ToolNode([get_schema_tool], name="get_schema")

# 执行SQL查询
run_query_tool = next(tool for tool in tools if tool.name == "sql_db_query")


# https://docs.langchain.com/oss/python/langgraph/sql-agent
# @tool(
#     run_query_tool.name,
#     description=run_query_tool.description,
#     args_schema=run_query_tool.args_schema,
# )
# def run_query_tool_with_interrupt(config: RunnableConfig, **tool_input):
#     request = {
#         "action": run_query_tool.name,
#         "args": tool_input,
#         "description": "Please review the tool call",
#     }
#     response = interrupt([request])
#     # approve the tool call
#     if response["type"] == "accept":
#         tool_response = run_query_tool.invoke(tool_input, config)
#     # update tool call args
#     elif response["type"] == "edit":
#         tool_input = response["args"]["args"]
#         tool_response = run_query_tool.invoke(tool_input, config)
#     # respond to the LLM with user feedback
#     elif response["type"] == "response":
#         user_feedback = response["args"]
#         tool_response = user_feedback
#     else:
#         raise ValueError(f"Unsupported interrupt response type: {response['type']}")

#     return tool_response


# run_query_node = ToolNode([run_query_tool_with_interrupt], name="run_query")

run_query_node = ToolNode([run_query_tool], name="run_query")


def list_tables(state: MessagesState):
    tool_call = {
        "name": "sql_db_list_tables",
        "args": {},
        "id": "abc123",
        "type": "tool_call",
    }
    # 初始化一个工具调用的AIMessage，包含工具调用：获取数据表列表
    tool_call_message = AIMessage(content="", tool_calls=[tool_call])

    list_tables_tool = next(tool for tool in tools if tool.name == "sql_db_list_tables")
    # 绑定获取数据表列表的工具调用，来执行这个工具调用
    tool_message = list_tables_tool.invoke(tool_call)
    response = AIMessage(f"Available tables: {tool_message.content}")

    return {"messages": [tool_call_message, tool_message, response]}


def call_get_schema(state: MessagesState):
    # 绑定获取数据库表结构的工具调用，来执行这个工具调用
    llm_with_tools = model.bind_tools([get_schema_tool], tool_choice="any")
    response = llm_with_tools.invoke(state["messages"])

    return {"messages": [response]}


generate_query_system_prompt = """
您是一个旨在与 SQL 数据库交互的代理。
给定一个输入问题，请创建一个语法正确的 {dialect} 查询并运行，然后查看查询结果并返回答案。除非用户指定要获取的示例数量，否则请始终将查询结果限制在最多 {top_k} 个。
您可以按相关列对结果进行排序，以返回数据库中最感兴趣的示例。切勿查询特定表中的所有列，而应仅查询与问题相关的列。
请勿对数据库执行任何 DML 语句（INSERT、UPDATE、DELETE、DROP 等）。
""".format(
    dialect=db.dialect,
    top_k=5,
)


def generate_query(state: MessagesState):
    system_message = {
        "role": "system",
        "content": generate_query_system_prompt,
    }

    llm_with_tools = model.bind_tools([run_query_tool])
    response = llm_with_tools.invoke([system_message] + state["messages"])

    return {"messages": [response]}


check_query_system_prompt = """
您是一位精通 SQL 且注重细节的专家。
请仔细检查 {dialect} 查询是否存在常见错误，包括：
- 对 NULL 值使用 NOT IN
- 应该使用 UNION ALL 而使用了 UNION
- 对互斥范围使用 BETWEEN
- 谓词中的数据类型不匹配
- 正确引用标识符
- 函数参数数量是否正确
- 数据类型是否正确转换
- 连接操作中使用的列是否正确

如果存在上述任何错误，请重写查询。如果没有错误，只需重现原始查询即可。
完成此检查后，您需要调用相应的工具来执行查询。
""".format(
    dialect=db.dialect
)


def check_query(state: MessagesState):
    system_message = {
        "role": "system",
        "content": check_query_system_prompt,
    }

    # Generate an artificial user message to check
    tool_call = state["messages"][-1].tool_calls[0]
    user_message = {"role": "user", "content": tool_call["args"]["query"]}
    llm_with_tools = model.bind_tools([run_query_tool], tool_choice="any")
    response = llm_with_tools.invoke([system_message, user_message])
    response.id = state["messages"][-1].id

    return {"messages": [response]}


def should_continue(state: MessagesState) -> Literal[END, "check_query"]:
    messages = state["messages"]
    last_message = messages[-1]
    if not last_message.tool_calls:
        return END
    else:
        return "check_query"


builder = StateGraph(MessagesState)
builder.add_node(list_tables)  # 1、列出数据库中的所有表
builder.add_node(call_get_schema)  # 2、调用获取数据库表结构的工具
builder.add_node(get_schema_node, "get_schema")  # 3、获取数据库表结构
builder.add_node(generate_query)  # 4、生成SQL查询
builder.add_node(check_query)  #
builder.add_node(run_query_node, "run_query")

builder.add_edge(START, "list_tables")
builder.add_edge("list_tables", "call_get_schema")
builder.add_edge("call_get_schema", "get_schema")
builder.add_edge("get_schema", "generate_query")
builder.add_conditional_edges(
    "generate_query",
    should_continue,
)
builder.add_edge("check_query", "run_query")
builder.add_edge("run_query", "generate_query")

# checkpointer = InMemorySaver()
graph = builder.compile()
