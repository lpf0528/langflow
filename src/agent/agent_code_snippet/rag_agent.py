"""
索引：从数据源中获取数据，并进行向量
检索和生成：从索引中检索相关数据，然后使用生成模型进行回答。
"""
import bs4
from langchain.agents import create_agent
from langchain_community.document_loaders import WebBaseLoader
from langchain_postgres import PGVector
from langchain_community.embeddings import OpenAIEmbeddings
from langchain_text_splitters import RecursiveCharacterTextSplitter

def load_splite_store(vector_store: PGVector):
    """加载、拆分、存储文档"""
    # https://docs.langchain.com/oss/python/langchain/rag#pgvector
    # 加载文档
    loader = WebBaseLoader(
        web_path = "https://lilianweng.github.io/posts/2023-06-23-agent/",
        bs_kwargs={
            "parse_only": bs4.SoupStrainer(
                class_=("post-content", "post-title", "post-header")
            )
        }
    )

    docs = loader.load()

    # 拆分文档
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000, chunk_overlap=100,
        add_start_index=True,  # track index in original document
    )
    splits = text_splitter.split_documents(docs)


    # 存储文档
    vector_store.add_documents(documents=splits)


def query_vector_store(vector_store: PGVector, query: str):
    """查询向量存储
    https://docs.langchain.com/oss/python/integrations/vectorstores/pgvector
    """
    
    # docs = vector_store.similarity_search(query, k=5, filter={"source": "https://lilianweng.github.io/posts/2023-06-23-agent/"})
    # for doc in docs:
    #     print(doc.page_content)
    #     print(doc.metadata)
    #     print("="*50)

    retriever = vector_store.as_retriever(search_type="mmr", search_kwargs={"k": 5}, filter={"source": "https://lilianweng.github.io/posts/2023-06-23-agent/"})
    docs = retriever.invoke(query)

    return docs
from langchain_core.tools import tool

# 构造一个检索上下文的工具:内容和工件
@tool(response_format="content_and_artifact")
def retrieve_context(query: str) -> str:
    """检索上下文"""
    docs = query_vector_store(vector_store, query)
    serialized  = "\n\n".join([(f"Source: {doc.metadata}\nContent: {doc.page_content}") for doc in docs])
    return serialized, docs

def rag_agent(query: str):
    """RAG代理"""
    # https://docs.langchain.com/oss/python/langchain/rag#expand-for-full-code-snippet
    tools = [retrieve_context]
    prompt  = "你可以访问一个从博客文章中检索上下文的工具。使用这个工具来帮助回答用户的问题。"
    agent = create_agent( model="gpt-3.5-turbo",tools=tools, system_prompt=prompt )    
    for item in agent.stream({'messages': [{'role': 'user', 'content': query}]}, stream_mode='values'):
        print(item['messages'][-1].pretty_print())



if __name__ == "__main__":
    
    embeddings =  OpenAIEmbeddings(model="text-embedding-ada-002")
    vector_store = PGVector(
        embeddings=embeddings,
        collection_name="my_docs",  # 文档集合
        connection="postgresql+psycopg://postgres:postgres@127.0.0.1:5432/sqlbot",
    )
    # load_splite_store(vector_store)
    # query_vector_store(vector_store, "What is the agent?")
    rag_agent("What is the agent?")