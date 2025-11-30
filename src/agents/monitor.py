import os
import json
import google.generativeai as genai
from typing import List
from src.tools.search import SearchTool
from dotenv import load_dotenv
import time

load_dotenv()

class MonitorAgent:
    def __init__(self):
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        self.search_tool = SearchTool()

    def scan(self, topic: str) -> List[str]:
        """
        Scans for trending claims or headlines related to a topic.
        """
        print(f"Scanning for news on: {topic}...")
        # Reduced from 10 to 5 for performance
        news_results = self.search_tool.news_search(topic, max_results=5)
        
        if not news_results:
            print("News search failed or empty. Trying text search...")
            news_results = self.search_tool.search(f"{topic} news", max_results=5)

        if not news_results:
            print("Search failed. Using mock data for demonstration.")
            news_results = [
                {"title": f"New study claims {topic} is accelerating faster than predicted", "body": "Scientists warn of irreversible tipping points."},
                {"title": f"Viral post claims {topic} is a hoax", "body": "Social media users share debunked theories."},
                {"title": f"Government announces new policy on {topic}", "body": "Legislation aims to reduce impact by 2030."}
            ]
        
        print(f"Found {len(news_results)} items.")

        prompt = f"""
        Analyze the following news headlines and snippets related to '{topic}'.
        Return 1-3 specific claims or statements that directly address the user's query: "{topic}".
        These should be the most relevant and important claims to verify.
        
        IMPORTANT: Return ONLY a valid JSON array (no markdown, no code blocks) like this:
        ["Claim 1", "Claim 2", "Claim 3"]

        News Data:
        {news_results}
        """

        # Retry logic for API calls
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(prompt)
                print(f"Gemini Raw Response: {response.text}")
                claims_text = response.text.strip()
                
                # Clean up any markdown code blocks
                claims_text = claims_text.replace("```json", "").replace("```python", "").replace("```", "").strip()
                
                # Parse JSON safely instead of using eval()
                claims = json.loads(claims_text)
                
                # Ensure we return max 3 claims
                if isinstance(claims, list):
                    return claims[:3]
                return [str(claims)]
                
            except json.JSONDecodeError as e:
                print(f"JSON parsing error (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                return []
            except Exception as e:
                print(f"Error in MonitorAgent (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                return []

