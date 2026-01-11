
from langchain_community.tools.tavily_search.tool import TavilySearchResults

LoggedTavilySearch = TavilySearchResults


if __name__ == "__main__":
    import dotenv
    dotenv.load_dotenv()

    search = LoggedTavilySearch(max_results=3)
    result = search.invoke("Agent未来两年的发展趋势")
    print(result)
