from duckduckgo_search import DDGS
from typing import List, Dict

class SearchTool:
    def __init__(self):
        pass

    def search(self, query: str, max_results: int = 5) -> List[Dict]:
        """
        Performs a DuckDuckGo search and returns a list of results.
        """
        try:
            with DDGS() as ddgs:
                results = list(ddgs.text(query, max_results=max_results))
            return results
        except Exception as e:
            print(f"Error during search: {e}")
            return []

    def news_search(self, query: str, max_results: int = 5) -> List[Dict]:
        """
        Performs a DuckDuckGo news search.
        """
        try:
            with DDGS() as ddgs:
                results = list(ddgs.news(query, max_results=max_results))
            return results
        except Exception as e:
            print(f"Error during news search: {e}")
            return []
