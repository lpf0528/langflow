
import enum
import os



class SearchEngine(enum.Enum):
    TAVILY = "tavily"
    # GOOGLE = "google"

SELECTED_SEARCH_ENGINE = os.getenv("SEARCH_API", SearchEngine.TAVILY.value)

