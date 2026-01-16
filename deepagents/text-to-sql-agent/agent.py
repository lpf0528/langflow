from dotenv import load_dotenv
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
from langchain.agents.middleware import HumanInTheLoopMiddleware
from langgraph.checkpoint.memory import InMemorySaver
import os
from langchain_openai import ChatOpenAI
from deepagents import create_deep_agent
from langchain.agents import create_agent
from prompts import db_prompt

load_dotenv()

# https://docs.langchain.com/oss/python/langchain/sql-agent#6-implement-human-in-the-loop-review


def create_sql_deep_agent():
    # 获取基本路径
    base_dir = os.path.dirname(os.path.abspath(__file__))
    db_path = os.path.join(base_dir, "chinook.db")
    # 1、配置数据库
    db = SQLDatabase.from_uri(
        # f"postgresql://postgres:postgres@localhost:5432/sqlbot",
        f"sqlite:///{db_path}",
        sample_rows_in_table_info=3,
    )
    # print(f"Dialect: {db.dialect}")  # 当前连接所用的数据库方言对象
    # print(f"Available tables: {db.get_usable_table_names()}") # 可用的数据表
    # print(f'Sample output: {db.run("SELECT * FROM user LIMIT 5;")}')

    model = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)
    # 2、为数据库添加工具
    toolkit = SQLDatabaseToolkit(db=db, llm=model)
    sql_tools = toolkit.get_tools()

    # 3、创建智能体

    agent = create_agent(
        model=model,
        tools=sql_tools,
        system_prompt=db_prompt.format(dialect=db.dialect, top_k=3),
        # 6、增加人类参与的审查
        middleware=[
            HumanInTheLoopMiddleware(
                interrupt_on={"sql_db_query": True},
                description_prefix="Tool execution pending approval",
            ),
        ],
        checkpointer=InMemorySaver(),
    )

    # 4、运行代理
    config = {"configurable": {"thread_id": "1"}}
    for step in agent.stream(
        {
            # 哪种音乐类型的歌曲平均时长最长？
            "messages": [
                {
                    "role": "user",
                    "content": "Which genre on average has the longest tracks?",
                }
            ]
        },
        stream_mode="values",
        config=config,
    ):
        if "__interrupt__" in step:
            print("__interrupt__")
            interrupt = step["__interrupt__"][0]
            for request in interrupt.value["action_requests"]:
                print(request["description"])
        else:
            print(step["messages"][-1].pretty_print())


def main():
    agent = create_sql_deep_agent()


if __name__ == "__main__":
    main()
