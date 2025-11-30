import os
import json
import google.generativeai as genai
from typing import Dict
from src.tools.search import SearchTool
from dotenv import load_dotenv
import time

load_dotenv()

class VerifierAgent:
    def __init__(self):
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        self.model = genai.GenerativeModel('gemini-2.0-flash')
        self.search_tool = SearchTool()

    def verify(self, claim: str) -> Dict:
        """
        Verifies a specific claim by cross-referencing with search results.
        """
        # Strategy: Run two searches to get broader context and specific fact checks
        print(f"Verifying claim: {claim}...")
        
        # 1. Direct search for the claim
        results_direct = self.search_tool.search(claim, max_results=3)
        # 2. Fact check specific search
        results_factcheck = self.search_tool.search(f"{claim} fact check truth", max_results=3)
        
        # Combine and deduplicate based on URL
        all_results = results_direct + results_factcheck
        seen_urls = set()
        unique_results = []
        for r in all_results:
            if r.get('href') not in seen_urls:
                unique_results.append(r)
                seen_urls.add(r.get('href'))
        
        if not unique_results:
            return {"status": "Unverified", "reason": "No evidence found", "evidence_data": []}

        prompt = f"""
        You are an expert misinformation analyst.
        Claim: "{claim}"

        Evidence from Web Search:
        {unique_results}

        Task:
        1. Analyze the evidence to determine the veracity of the claim.
        2. Assign a status: "Verified Fact", "Misinformation", "Misleading", or "Unverified".
        3. Select the top 3 most credible sources from the evidence list to support your decision.

        IMPORTANT: Return ONLY a valid JSON object (no markdown, no code blocks) in this exact format:
        {{
            "status": "Verified Fact" | "Misinformation" | "Misleading" | "Unverified",
            "explanation": "Clear, concise summary of why this is true/false...",
            "sources": ["Source Name 1", "Source Name 2"]
        }}
        """

        # Retry logic for API calls
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(prompt)
                result_text = response.text.strip()
                
                # Clean up any markdown code blocks
                result_text = result_text.replace("```json", "").replace("```python", "").replace("```", "").strip()
                
                # Parse JSON safely instead of using eval()
                verification_result = json.loads(result_text)
                
                # Validate required fields
                if "status" not in verification_result:
                    raise ValueError("Missing 'status' field in response")
                
                # Attach raw search results for the frontend to display links
                verification_result['evidence_data'] = unique_results[:5]  # Limit to 5
                return verification_result
                
            except json.JSONDecodeError as e:
                print(f"JSON parsing error (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)  # Wait before retry
                    continue
                return {
                    "status": "Error", 
                    "explanation": "Failed to parse verification result",
                    "evidence_data": unique_results[:5]
                }
            except Exception as e:
                print(f"Error in VerifierAgent (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                return {
                    "status": "Error", 
                    "explanation": str(e),
                    "evidence_data": unique_results[:5]
                }

