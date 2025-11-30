import os
import google.generativeai as genai
from typing import Dict
from dotenv import load_dotenv
import time

load_dotenv()

class ExplainerAgent:
    def __init__(self):
        genai.configure(api_key=os.getenv("GOOGLE_API_KEY"))
        self.model = genai.GenerativeModel('gemini-2.0-flash')

    def explain(self, claim: str, verification_result: Dict) -> str:
        """
        Generates a clear, accessible explanation of the verification.
        """
        print(f"Generating explanation for: {claim}...")

        prompt = f"""
        You are a helpful AI assistant dedicated to fighting misinformation.
        
        Claim: "{claim}"
        Verification Status: {verification_result.get('status')}
        Fact-Check Details: {verification_result.get('explanation')}
        Sources: {verification_result.get('sources')}

        Task:
        Write a short, empathetic, and clear explanation for a general audience.
        - If the claim is false, explain *why* it's false and what the truth is.
        - If it's true, confirm it with context.
        - Use a friendly but authoritative tone.
        - Format with Markdown (use bolding for key points).
        - Keep it concise (2-3 paragraphs maximum).
        """

        # Retry logic for API calls
        max_retries = 3
        for attempt in range(max_retries):
            try:
                response = self.model.generate_content(prompt)
                if response and response.text:
                    return response.text
                raise ValueError("Empty response from API")
            except Exception as e:
                print(f"Error in ExplainerAgent (attempt {attempt + 1}/{max_retries}): {e}")
                if attempt < max_retries - 1:
                    time.sleep(1)
                    continue
                return "Could not generate explanation. Please try again."

