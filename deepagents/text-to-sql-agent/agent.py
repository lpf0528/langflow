from dotenv import load_dotenv
from langchain_community.utilities import SQLDatabase
from langchain_community.agent_toolkits import SQLDatabaseToolkit
import os
from langchain_openai import ChatOpenAI
from deepagents import create_deep_agent

load_dotenv()


def create_sql_deep_agent():
    # 获取基本路径
    # base_dir = os.path.dirname(os.path.abspath(__file__))
    # db_path = os.path.join(base_dir, "chinook.db")
    # 配置数据库
    db = SQLDatabase.from_uri(
        # f"postgresql://postgres:postgres@localhost:5432/sqlbot",
        f"sqlite:///sqlbot.db",
        sample_rows_in_table_info=3,
    )
    model = ChatOpenAI(model_name="gpt-3.5-turbo", temperature=0)
    toolkit = SQLDatabaseToolkit(db=db, llm=model)
    sql_tools = toolkit.get_tools()
    print(sql_tools)
    print(f"Dialect: {db.dialect}")
    print(f"Available tables: {db.get_usable_table_names()}")
    print(f'Sample output: {db.run("SELECT * FROM user LIMIT 5;")}')


# agent = create_deep_agent(
#     model=model,
#     memory=["./AGENTS.md"],
#     skills=["./skills/"],
#     toolkit=toolkit,
#     verbose=True,
# )
# C:\Users\EDY\AppData\Roaming\Tencent\WXWork\VoipRecords


def main():
    agent = create_sql_deep_agent()


if __name__ == "__main__":
    main()
